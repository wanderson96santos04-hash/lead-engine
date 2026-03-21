import csv
import os
import re
import time
import unicodedata
from collections import defaultdict

import requests


BASE_KEYWORDS = [
    "cidadania italiana demora quanto tempo",
    "cidadania italiana vale a pena",
    "cidadania italiana por casamento",
    "cidadania italiana para filhos",
    "cidadania italiana para menores",
    "cidadania italiana precisa falar italiano",
    "cidadania italiana precisa ir para itália",
    "cidadania italiana limite de gerações",
    "cidadania italiana por descendência materna",
    "cidadania italiana linha materna",
    "cidadania italiana nome errado na certidão",
    "cidadania italiana retificação de documentos",
    "cidadania italiana certidão em inteiro teor",
    "cidadania italiana apostilamento de haia",
    "cidadania italiana tradução juramentada",
    "cidadania italiana consulado",
    "cidadania italiana agendamento consulado",
    "cidadania italiana via judicial demora",
    "cidadania italiana via judicial vale a pena",
    "cidadania italiana benefícios",
    "passaporte italiano vantagens",
    "dupla cidadania italiana como funciona",
    "sobrenome italiano ajuda na cidadania",
    "como saber se tenho direito à cidadania italiana",
]

EXPANSION_SUFFIXES = [
    "",
    " o que é",
    " como funciona",
    " vale a pena",
    " demora quanto tempo",
    " 2026",
    " no brasil",
    " na itália",
    " via judicial",
    " no consulado",
    " precisa de advogado",
    " precisa de tradução",
    " precisa apostilar",
    " precisa retificar documentos",
    " para filhos",
    " para menor de idade",
]

COMMERCIAL_TERMS = [
    "quanto custa",
    "preço",
    "valor",
    "vale a pena",
    "advogado",
    "assessoria",
]

QUALIFICATION_TERMS = [
    "quem tem direito",
    "tenho direito",
    "sobrenome",
    "sobrenomes",
    "descendência",
    "descendente",
    "antepassado",
    "italiano",
    "linha materna",
    "filhos",
    "menor de idade",
]

DOCUMENT_TERMS = [
    "documento",
    "documentos",
    "certidão",
    "certidoes",
    "registro",
    "registros",
    "retificação",
    "retificacao",
    "inteiro teor",
    "apostila",
    "apostilamento",
    "tradução",
    "traducao",
]

PROCESS_TERMS = [
    "como tirar",
    "como fazer",
    "como funciona",
    "passo a passo",
    "prazo",
    "tempo",
    "demora",
    "via judicial",
    "consulado",
    "no brasil",
    "na itália",
    "agendamento",
]

LOCAL_MODIFIERS = [
    "são paulo",
    "rio de janeiro",
    "belo horizonte",
    "minas gerais",
    "curitiba",
    "porto alegre",
    "campinas",
    "brasília",
    "salvador",
    "recife",
]

NEGATIVE_TERMS = [
    "youtube",
    "tiktok",
    "pdf",
    "download",
    "imagem",
    "imagens",
    "meme",
    "frases",
    "wikipedia",
    "novela",
    "filme",
]

BLOCKED_BRAND_TERMS = [
    "notaro",
    "euro consultoria",
    "cidadania express",
    "reclame aqui",
    "telefone",
    "whatsapp",
    "endereço",
    "endereco",
    "avaliações",
    "avaliacoes",
    "review",
]

FORCED_BAD_COMBINATIONS = [
    ("sobrenomes italianos", "quanto custa"),
    ("sobrenomes italianos", "preço"),
    ("sobrenomes italianos", "valor"),
    ("sobrenomes italianos", "via judicial"),
    ("sobrenomes italianos", "por casamento"),
    ("cidadania italiana por casamento", "quanto custa"),
    ("cidadania italiana para filhos", "quanto custa"),
    ("cidadania italiana para menores", "quanto custa"),
]

# artigos/intenções já publicadas ou já canibalizadas
EXCLUDED_KEYWORDS = [
    "cidadania italiana quanto custa",
    "como tirar cidadania italiana quanto custa",
    "tirar cidadania italiana quanto custa",
    "cidadania italiana via judicial quanto custa",
    "quanto custa cidadania italiana por descendência",
    "quem tem direito cidadania italiana",
    "documentos cidadania italiana",
    "documentos cidadania italiana no brasil",
    "documentos cidadania italiana via judicial",
    "documentos para cidadania italiana via judicial",
    "como tirar cidadania italiana quais documentos",
    "como tirar cidadania italiana sem documentos",
]

# palavras que não queremos mais como seed principal para não repetir intenção
BLOCKED_SEED_PATTERNS = [
    "quanto custa cidadania italiana",
    "cidadania italiana quanto custa",
    "documentos cidadania italiana",
    "quem tem direito cidadania italiana",
    "como tirar cidadania italiana",
]

OUTPUT_DIR = "../data"
OUTPUT_TXT = os.path.join(OUTPUT_DIR, "keywords.txt")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "keywords_map.csv")

SUGGEST_URL = "https://suggestqueries.google.com/complete/search"


def normalize(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"\s+", " ", text)
    return text


def slugify(text: str) -> str:
    text = normalize(text)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def has_any_term(keyword: str, terms: list[str]) -> bool:
    kw = normalize(keyword)
    return any(normalize(term) in kw for term in terms)


def has_blocked_brand(keyword: str) -> bool:
    kw = normalize(keyword)
    return any(term in kw for term in BLOCKED_BRAND_TERMS)


def has_negative_term(keyword: str) -> bool:
    kw = normalize(keyword)
    return any(term in kw for term in NEGATIVE_TERMS)


def is_forced_bad_combination(keyword: str) -> bool:
    kw = normalize(keyword)
    for left, right in FORCED_BAD_COMBINATIONS:
        if normalize(left) in kw and normalize(right) in kw:
            return True
    return False


def token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", normalize(text)))


def is_too_close_to_excluded(keyword: str) -> bool:
    kw = normalize(keyword)
    kw_tokens = token_set(kw)

    for existing in EXCLUDED_KEYWORDS:
        existing_norm = normalize(existing)

        if kw == existing_norm:
            return True

        existing_tokens = token_set(existing_norm)

        # bloqueia slugs/intenção quase iguais
        intersection = kw_tokens & existing_tokens
        union = kw_tokens | existing_tokens
        similarity = len(intersection) / max(len(union), 1)

        if similarity >= 0.72:
            return True

        # bloqueio adicional para temas muito sensíveis à canibalização
        if (
            "quanto custa" in kw and "quanto custa" in existing_norm and "cidadania italiana" in kw
        ):
            return True

        if (
            "documentos" in kw and "cidadania italiana" in kw and "documentos" in existing_norm
        ):
            return True

        if (
            "quem tem direito" in kw and "cidadania italiana" in kw and "quem tem direito" in existing_norm
        ):
            return True

        if (
            "como tirar" in kw and "cidadania italiana" in kw and "como tirar" in existing_norm
        ):
            return True

    return False


def is_natural_keyword(keyword: str) -> bool:
    kw = normalize(keyword)

    if len(kw) < 10:
        return False

    if has_negative_term(kw):
        return False

    if has_blocked_brand(kw):
        return False

    if not any(token in kw for token in ["cidadania", "italiana", "italiano", "italianos", "passaporte"]):
        return False

    if is_forced_bad_combination(kw):
        return False

    if is_too_close_to_excluded(kw):
        return False

    if "preço preço" in kw or "valor valor" in kw:
        return False

    if kw.count("quem tem direito") > 1:
        return False

    if "sobrenomes italianos" in kw and has_any_term(
        kw, ["quanto custa", "preço", "valor", "via judicial", "por casamento"]
    ):
        return False

    if has_any_term(kw, LOCAL_MODIFIERS):
        if len(kw.split()) > 7 and not has_any_term(
            kw, ["consulado", "agendamento", "documentos", "prazo", "tempo"]
        ):
            return False

    if len(kw.split()) >= 8 and not has_any_term(
        kw,
        QUALIFICATION_TERMS + DOCUMENT_TERMS + PROCESS_TERMS + COMMERCIAL_TERMS
    ):
        return False

    return True


def classify_intent(keyword: str) -> str:
    kw = normalize(keyword)

    if has_any_term(kw, COMMERCIAL_TERMS):
        return "commercial"
    if has_any_term(kw, DOCUMENT_TERMS):
        return "documents"
    if has_any_term(kw, PROCESS_TERMS):
        return "process"
    if has_any_term(kw, QUALIFICATION_TERMS):
        return "qualification"
    return "informational"


def classify_cluster(keyword: str) -> str:
    kw = normalize(keyword)

    if has_any_term(kw, LOCAL_MODIFIERS):
        return "local"
    if has_any_term(kw, ["sobrenome", "sobrenomes", "quem tem direito", "descend", "linha materna", "filhos"]):
        return "eligibility"
    if has_any_term(kw, DOCUMENT_TERMS):
        return "documents"
    if has_any_term(kw, PROCESS_TERMS):
        return "process"
    if has_any_term(kw, COMMERCIAL_TERMS):
        return "cost"
    return "general"


def score(keyword: str) -> int:
    kw = normalize(keyword)
    s = 0

    if "cidadania italiana" in kw:
        s += 18

    if has_any_term(kw, QUALIFICATION_TERMS):
        s += 24

    if has_any_term(kw, DOCUMENT_TERMS):
        s += 22

    if has_any_term(kw, PROCESS_TERMS):
        s += 18

    if has_any_term(kw, COMMERCIAL_TERMS):
        s += 16

    if has_any_term(kw, LOCAL_MODIFIERS):
        s += 10

    if 4 <= len(kw.split()) <= 7:
        s += 10

    if "2026" in kw:
        s += 3

    # bônus para temas menos canibalizados e muito úteis
    if has_any_term(kw, ["linha materna", "filhos", "menor de idade", "apostilamento", "tradução", "retificação"]):
        s += 12

    if has_any_term(kw, ["demora quanto tempo", "vale a pena", "como funciona"]):
        s += 8

    return s


def priority(score_value: int) -> str:
    if score_value >= 52:
        return "P1"
    if score_value >= 34:
        return "P2"
    return "P3"


def get_suggestions(session: requests.Session, query: str) -> list[str]:
    try:
        response = session.get(
            SUGGEST_URL,
            params={"client": "firefox", "hl": "pt-BR", "q": query},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        suggestions = data[1] if isinstance(data, list) and len(data) > 1 else []
        return [s for s in suggestions if isinstance(s, str) and s.strip()]
    except Exception:
        return []


def build_seed_queries() -> list[str]:
    seeds = []

    for base in BASE_KEYWORDS:
        for suffix in EXPANSION_SUFFIXES:
            combined = (base + suffix).strip()
            if not has_any_term(combined, BLOCKED_SEED_PATTERNS):
                seeds.append(combined)

    for city in LOCAL_MODIFIERS:
        seeds.append(f"cidadania italiana consulado {city}")
        seeds.append(f"agendamento cidadania italiana {city}")
        seeds.append(f"documentos cidadania italiana {city}")

    unique = []
    seen = set()

    for seed in seeds:
        key = normalize(seed)
        if key not in seen and not is_too_close_to_excluded(key):
            seen.add(key)
            unique.append(seed)

    return unique


def should_keep_seed(seed: str) -> bool:
    return is_natural_keyword(seed)


def generate() -> list[dict]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/146.0.0.0 Safari/537.36"
            )
        }
    )

    all_keywords = set()
    seeds = build_seed_queries()

    for i, seed in enumerate(seeds, start=1):
        print(f"[{i}/{len(seeds)}] {seed}")

        suggestions = get_suggestions(session, seed)

        for suggestion in suggestions:
            all_keywords.add(suggestion)

        if should_keep_seed(seed):
            all_keywords.add(seed)

        time.sleep(0.2)

    final_rows = {}
    for kw in all_keywords:
        normalized_kw = normalize(kw)

        if not is_natural_keyword(normalized_kw):
            continue

        row_score = score(normalized_kw)

        final_rows[normalized_kw] = {
            "keyword": normalized_kw,
            "slug": slugify(normalized_kw),
            "intent": classify_intent(normalized_kw),
            "cluster": classify_cluster(normalized_kw),
            "priority": priority(row_score),
            "score": row_score,
        }

    rows = list(final_rows.values())
    rows.sort(key=lambda x: (-x["score"], x["keyword"]))
    return rows


def save(rows: list[dict]) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(row["keyword"] + "\n")

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["keyword", "slug", "intent", "cluster", "priority", "score"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} keywords salvas")
    print(f"- {OUTPUT_TXT}")
    print(f"- {OUTPUT_CSV}")


def print_summary(rows: list[dict]) -> None:
    intent_count = defaultdict(int)
    cluster_count = defaultdict(int)
    priority_count = defaultdict(int)

    for row in rows:
        intent_count[row["intent"]] += 1
        cluster_count[row["cluster"]] += 1
        priority_count[row["priority"]] += 1

    print("\nResumo por intenção:")
    for key in sorted(intent_count.keys()):
        print(f"- {key}: {intent_count[key]}")

    print("\nResumo por cluster:")
    for key in sorted(cluster_count.keys()):
        print(f"- {key}: {cluster_count[key]}")

    print("\nResumo por prioridade:")
    for key in sorted(priority_count.keys()):
        print(f"- {key}: {priority_count[key]}")


if __name__ == "__main__":
    rows = generate()
    save(rows)
    print_summary(rows)