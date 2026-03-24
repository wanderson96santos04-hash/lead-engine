import csv
import os
import re
import unicodedata
from datetime import datetime

DAILY_TARGET = 5

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "../data"))

KEYWORDS_MAP_PATH = os.path.join(DATA_DIR, "keywords_map.csv")
USED_KEYWORDS_PATH = os.path.join(DATA_DIR, "used_keywords.txt")
KEYWORDS_LOG_PATH = os.path.join(DATA_DIR, "keywords_log.csv")

STOPWORDS = {
    "a", "o", "e", "de", "da", "do", "das", "dos", "na", "no", "nas", "nos",
    "para", "com", "como", "se", "em", "por", "quanto", "tempo", "que", "ao",
    "à", "as", "os", "um", "uma"
}

BAD_TERMS = {
    "gratis", "grátis", "youtube", "tiktok", "pdf", "download", "wikipedia",
    "telefone", "whatsapp", "reclame", "review", "cupom", "desconto", "curso"
}

TOPIC_LIBRARY = [
    {
        "base": "cidadania italiana linha materna",
        "cluster": "eligibility",
        "intent": "qualification",
        "score_boost": 16,
        "patterns": [
            "{base} como funciona",
            "{base} demora quanto tempo",
            "{base} precisa de advogado",
            "{base} vale a pena",
            "{base} no consulado como funciona",
            "{base} via judicial como funciona",
            "{base} precisa de traducao",
            "{base} precisa apostilar",
            "{base} para filhos como funciona",
            "{base} nascidos antes de 1948 como funciona",
        ],
    },
    {
        "base": "cidadania italiana para filhos",
        "cluster": "eligibility",
        "intent": "qualification",
        "score_boost": 16,
        "patterns": [
            "{base} como funciona",
            "{base} demora quanto tempo",
            "{base} precisa de traducao",
            "{base} precisa apostilar",
            "{base} via judicial como funciona",
            "{base} no consulado como funciona",
            "{base} vale a pena",
            "{base} maiores de idade como funciona",
            "{base} menores de idade como funciona",
            "{base} precisa de advogado",
        ],
    },
    {
        "base": "cidadania italiana traducao juramentada",
        "cluster": "documents",
        "intent": "documents",
        "score_boost": 15,
        "patterns": [
            "{base} como funciona",
            "{base} demora quanto tempo",
            "{base} precisa apostilar",
            "{base} vale a pena",
            "{base} no brasil como funciona",
            "{base} na italia como funciona",
            "{base} precisa de advogado",
            "{base} para cidadania italiana como funciona",
        ],
    },
    {
        "base": "cidadania italiana apostilamento de haia",
        "cluster": "documents",
        "intent": "documents",
        "score_boost": 15,
        "patterns": [
            "{base} como funciona",
            "{base} demora quanto tempo",
            "{base} precisa de traducao",
            "{base} vale a pena",
            "{base} no brasil como funciona",
            "{base} para cidadania italiana como funciona",
            "{base} precisa de advogado",
            "{base} quando e necessario",
        ],
    },
    {
        "base": "cidadania italiana nome errado na certidao",
        "cluster": "documents",
        "intent": "documents",
        "score_boost": 15,
        "patterns": [
            "{base} como funciona",
            "{base} como resolver",
            "{base} precisa retificar",
            "{base} demora quanto tempo",
            "{base} atrapalha o processo",
            "{base} vale a pena corrigir",
            "{base} precisa de advogado",
            "{base} impede cidadania italiana",
        ],
    },
    {
        "base": "cidadania italiana via judicial",
        "cluster": "process",
        "intent": "commercial",
        "score_boost": 15,
        "patterns": [
            "{base} como funciona",
            "{base} demora quanto tempo",
            "{base} vale a pena",
            "{base} quanto custa",
            "{base} precisa de advogado",
            "{base} para linha materna como funciona",
            "{base} para filhos como funciona",
            "{base} ainda vale a pena",
            "{base} compensa no brasil",
        ],
    },
    {
        "base": "como saber se tenho direito a cidadania italiana",
        "cluster": "eligibility",
        "intent": "qualification",
        "score_boost": 17,
        "patterns": [
            "{base} pelo sobrenome",
            "{base} com poucos documentos",
            "{base} pela linha materna",
            "{base} para filhos",
            "{base} antes de investir",
            "{base} pela certidao de nascimento",
            "{base} sem documentos italianos",
            "{base} pelo nome da familia",
        ],
    },
    {
        "base": "cidadania italiana consulado",
        "cluster": "process",
        "intent": "process",
        "score_boost": 13,
        "patterns": [
            "{base} como funciona",
            "{base} demora quanto tempo",
            "{base} precisa de traducao",
            "{base} vale a pena",
            "{base} no brasil como funciona",
            "{base} fila de espera como funciona",
            "{base} agendamento como funciona",
        ],
    },
    {
        "base": "cidadania italiana certidao em inteiro teor",
        "cluster": "documents",
        "intent": "documents",
        "score_boost": 14,
        "patterns": [
            "{base} como funciona",
            "{base} demora quanto tempo",
            "{base} precisa apostilar",
            "{base} precisa de traducao",
            "{base} vale a pena pedir antes",
            "{base} para cidadania italiana como funciona",
            "{base} onde pedir no brasil",
        ],
    },
    {
        "base": "cidadania italiana retificacao de certidao",
        "cluster": "documents",
        "intent": "documents",
        "score_boost": 14,
        "patterns": [
            "{base} como funciona",
            "{base} demora quanto tempo",
            "{base} vale a pena",
            "{base} precisa de advogado",
            "{base} para nome errado como funciona",
            "{base} antes da cidadania italiana",
            "{base} quando e necessaria",
        ],
    },
    {
        "base": "cidadania italiana busca de certidoes",
        "cluster": "documents",
        "intent": "documents",
        "score_boost": 13,
        "patterns": [
            "{base} como funciona",
            "{base} na italia como funciona",
            "{base} demora quanto tempo",
            "{base} vale a pena",
            "{base} sem saber o comune",
            "{base} com poucos dados da familia",
        ],
    },
    {
        "base": "cidadania italiana naturalizacao do ascendente",
        "cluster": "eligibility",
        "intent": "qualification",
        "score_boost": 15,
        "patterns": [
            "{base} como saber",
            "{base} como funciona",
            "{base} impede o processo",
            "{base} atrapalha a cidadania italiana",
            "{base} como consultar",
            "{base} antes de entrar no processo",
        ],
    },
    {
        "base": "cidadania italiana por casamento",
        "cluster": "process",
        "intent": "commercial",
        "score_boost": 12,
        "patterns": [
            "{base} como funciona",
            "{base} demora quanto tempo",
            "{base} vale a pena",
            "{base} precisa falar italiano",
            "{base} quanto custa",
            "{base} no brasil como funciona",
            "{base} precisa morar na italia",
        ],
    },
    {
        "base": "cidadania italiana aire",
        "cluster": "process",
        "intent": "process",
        "score_boost": 11,
        "patterns": [
            "{base} como funciona",
            "{base} o que e",
            "{base} para que serve",
            "{base} e obrigatorio",
            "{base} como fazer cadastro",
            "{base} demora quanto tempo",
        ],
    },
    {
        "base": "passaporte italiano depois da cidadania",
        "cluster": "process",
        "intent": "process",
        "score_boost": 11,
        "patterns": [
            "{base} como tirar",
            "{base} demora quanto tempo",
            "{base} quanto custa",
            "{base} vale a pena fazer no brasil",
            "{base} quais documentos precisa",
        ],
    },
]

ROTATION_ORDER = ["eligibility", "documents", "process", "cost", "general"]


def normalize(text: str) -> str:
    text = (text or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text)
    return text


def slugify(text: str) -> str:
    text = normalize(text)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def keyword_tokens(text: str) -> set[str]:
    text = normalize(text)
    words = re.findall(r"[a-z0-9]+", text)
    return {w for w in words if w not in STOPWORDS}


def load_used_keywords() -> set[str]:
    used = set()

    if os.path.exists(USED_KEYWORDS_PATH):
        with open(USED_KEYWORDS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                kw = normalize(line.strip())
                if kw:
                    used.add(kw)

    if os.path.exists(KEYWORDS_LOG_PATH):
        with open(KEYWORDS_LOG_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                kw = normalize((row.get("keyword") or "").strip())
                if kw:
                    used.add(kw)

    return used


def load_log_count() -> int:
    if not os.path.exists(KEYWORDS_LOG_PATH):
        return 0

    with open(KEYWORDS_LOG_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return sum(1 for _ in reader)


def has_bad_term(keyword: str) -> bool:
    kw = normalize(keyword)
    return any(term in kw for term in BAD_TERMS)


def looks_like_real_search(keyword: str) -> bool:
    kw = normalize(keyword)

    if len(kw.split()) < 5:
        return False

    if "cidadania italiana" not in kw and "passaporte italiano" not in kw:
        return False

    if has_bad_term(kw):
        return False

    duplicated_patterns = [
        "vale a pena vale a pena",
        "como funciona como funciona",
        "demora quanto tempo demora quanto tempo",
        "precisa de advogado precisa de advogado",
    ]
    if any(x in kw for x in duplicated_patterns):
        return False

    return True


def detect_intent(keyword: str) -> str:
    kw = normalize(keyword)

    if any(x in kw for x in ["quanto custa", "vale a pena", "precisa de advogado", "compensa", "investir"]):
        return "commercial"

    if any(x in kw for x in ["documento", "documentos", "certidao", "certidão", "traducao", "tradução", "apostilamento", "apostilar", "retificacao", "retificação"]):
        return "documents"

    if any(x in kw for x in ["como saber se tenho direito", "direito", "linha materna", "sobrenome", "ascendente", "filhos"]):
        return "qualification"

    if any(x in kw for x in ["como funciona", "demora quanto tempo", "consulado", "via judicial", "aire", "passaporte"]):
        return "process"

    return "informational"


def detect_cluster(keyword: str) -> str:
    kw = normalize(keyword)

    if any(x in kw for x in ["certidao", "certidão", "traducao", "tradução", "apostilamento", "retificar", "retificacao", "retificação", "documentos", "inteiro teor"]):
        return "documents"

    if any(x in kw for x in ["linha materna", "filhos", "direito", "sobrenome", "ascendente", "naturalizacao"]):
        return "eligibility"

    if any(x in kw for x in ["quanto custa", "vale a pena", "precisa de advogado", "compensa", "investir"]):
        return "cost"

    if any(x in kw for x in ["como funciona", "demora quanto tempo", "consulado", "via judicial", "aire", "passaporte"]):
        return "process"

    return "general"


def score_keyword(keyword: str, boost: int = 0) -> int:
    kw = normalize(keyword)
    score = 0

    if "cidadania italiana" in kw:
        score += 25

    if any(x in kw for x in ["linha materna", "filhos", "direito", "sobrenome", "ascendente"]):
        score += 18

    if any(x in kw for x in ["certidao", "certidão", "traducao", "tradução", "apostilamento", "retificacao", "retificação", "documentos", "inteiro teor"]):
        score += 17

    if any(x in kw for x in ["como funciona", "demora quanto tempo", "via judicial", "consulado", "aire", "passaporte"]):
        score += 16

    if any(x in kw for x in ["quanto custa", "vale a pena", "precisa de advogado", "compensa"]):
        score += 14

    if 5 <= len(kw.split()) <= 10:
        score += 8

    score += boost
    return min(score, 99)


def priority_from_score(score: int) -> str:
    if score >= 80:
        return "P1"
    if score >= 60:
        return "P2"
    return "P3"


def is_near_duplicate(candidate: str, existing_keywords: set[str]) -> bool:
    cand_norm = normalize(candidate)
    cand_slug = slugify(candidate)
    cand_tokens = keyword_tokens(candidate)

    for existing in existing_keywords:
        ex_norm = normalize(existing)
        ex_slug = slugify(existing)
        ex_tokens = keyword_tokens(existing)

        if cand_norm == ex_norm:
            return True

        if cand_slug == ex_slug:
            return True

        if cand_tokens and ex_tokens:
            inter = len(cand_tokens & ex_tokens)
            union = len(cand_tokens | ex_tokens)
            similarity = inter / union if union else 0

            if similarity >= 0.85:
                return True

            smaller = min(len(cand_tokens), len(ex_tokens))
            if smaller > 0 and inter / smaller >= 0.9:
                return True

    return False


def build_candidate_pool() -> list[dict]:
    pool = []

    for topic in TOPIC_LIBRARY:
        for pattern in topic["patterns"]:
            keyword = normalize(pattern.format(base=topic["base"]))

            if not looks_like_real_search(keyword):
                continue

            score = score_keyword(keyword, topic["score_boost"])
            intent = detect_intent(keyword)
            cluster = detect_cluster(keyword)
            priority = priority_from_score(score)

            pool.append({
                "keyword": keyword,
                "slug": slugify(keyword),
                "intent": intent if intent != "informational" else topic["intent"],
                "cluster": cluster if cluster != "general" else topic["cluster"],
                "priority": priority,
                "score": score,
            })

    unique = {}
    for row in pool:
        unique[row["keyword"]] = row

    return sorted(unique.values(), key=lambda x: (-x["score"], x["keyword"]))


def choose_cluster_rotation(day_index: int) -> list[str]:
    shift = day_index % len(ROTATION_ORDER)
    return ROTATION_ORDER[shift:] + ROTATION_ORDER[:shift]


def select_daily_keywords(pool: list[dict], used_keywords: set[str], target: int = DAILY_TARGET) -> list[dict]:
    selected = []
    temp_seen = set(used_keywords)

    day_index = load_log_count() // DAILY_TARGET
    cluster_rotation = choose_cluster_rotation(day_index)

    # 1. tenta diversidade por cluster
    for cluster in cluster_rotation:
        for row in pool:
            if len(selected) >= target:
                break

            kw = row["keyword"]
            if row["cluster"] != cluster:
                continue
            if is_near_duplicate(kw, temp_seen):
                continue

            selected.append(row)
            temp_seen.add(kw)
            break

        if len(selected) >= target:
            break

    # 2. completa por score
    for row in pool:
        if len(selected) >= target:
            break

        kw = row["keyword"]
        if is_near_duplicate(kw, temp_seen):
            continue

        selected.append(row)
        temp_seen.add(kw)

    return selected


def save_keywords_map(rows: list[dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(KEYWORDS_MAP_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["keyword", "slug", "intent", "cluster", "priority", "score"]
        )
        writer.writeheader()
        writer.writerows(rows)


def append_used_keywords(rows: list[dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    existing = set()
    if os.path.exists(USED_KEYWORDS_PATH):
        with open(USED_KEYWORDS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                kw = normalize(line.strip())
                if kw:
                    existing.add(kw)

    with open(USED_KEYWORDS_PATH, "a", encoding="utf-8") as f:
        for row in rows:
            kw = normalize(row["keyword"])
            if kw not in existing:
                f.write(kw + "\n")
                existing.add(kw)


def append_keywords_log(rows: list[dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    file_exists = os.path.exists(KEYWORDS_LOG_PATH)

    with open(KEYWORDS_LOG_PATH, "a", encoding="utf-8", newline="") as f:
        fieldnames = ["date", "keyword", "slug", "intent", "cluster", "priority", "score"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        today = datetime.now().strftime("%Y-%m-%d")
        for row in rows:
            writer.writerow({
                "date": today,
                "keyword": row["keyword"],
                "slug": row["slug"],
                "intent": row["intent"],
                "cluster": row["cluster"],
                "priority": row["priority"],
                "score": row["score"],
            })


def print_summary(rows: list[dict]) -> None:
    print("\n5 keywords geradas com sucesso:\n")
    for i, row in enumerate(rows, start=1):
        print(
            f"{i}. {row['keyword']} | "
            f"intent={row['intent']} | cluster={row['cluster']} | "
            f"priority={row['priority']} | score={row['score']}"
        )

    print(f"\nArquivo criado: {KEYWORDS_MAP_PATH}")
    print(f"Histórico: {USED_KEYWORDS_PATH}")
    print(f"Log: {KEYWORDS_LOG_PATH}")


def main():
    used_keywords = load_used_keywords()
    pool = build_candidate_pool()
    selected = select_daily_keywords(pool, used_keywords, DAILY_TARGET)

    if len(selected) < DAILY_TARGET:
        raise RuntimeError(
            f"Não foi possível gerar {DAILY_TARGET} keywords novas sem repetição. "
            f"Gerei apenas {len(selected)}."
        )

    save_keywords_map(selected)
    append_used_keywords(selected)
    append_keywords_log(selected)
    print_summary(selected)


if __name__ == "__main__":
    main()