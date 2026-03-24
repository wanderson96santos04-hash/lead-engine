import csv
import os
import random
import re
import unicodedata
from datetime import datetime
from itertools import product

DAILY_TARGET = 5

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "../data"))

KEYWORDS_MAP_PATH = os.path.join(DATA_DIR, "keywords_map.csv")
USED_KEYWORDS_PATH = os.path.join(DATA_DIR, "used_keywords.txt")
KEYWORDS_LOG_PATH = os.path.join(DATA_DIR, "keywords_log.csv")

# ----------------------------
# CONFIG SEO DO NICHO
# ----------------------------

PRIMARY_TOPICS = [
    {
        "topic": "cidadania italiana linha materna",
        "cluster": "eligibility",
        "intent": "process",
        "priority_base": 90,
        "patterns": [
            "cidadania italiana linha materna demora quanto tempo",
            "cidadania italiana linha materna como funciona",
            "cidadania italiana linha materna precisa de advogado",
            "cidadania italiana linha materna vale a pena",
            "cidadania italiana linha materna no consulado como funciona",
            "cidadania italiana linha materna via judicial como funciona",
        ],
    },
    {
        "topic": "cidadania italiana para filhos",
        "cluster": "eligibility",
        "intent": "process",
        "priority_base": 90,
        "patterns": [
            "cidadania italiana para filhos demora quanto tempo",
            "cidadania italiana para filhos como funciona",
            "cidadania italiana para filhos precisa de traducao",
            "cidadania italiana para filhos no consulado como funciona",
            "cidadania italiana para filhos via judicial como funciona",
            "cidadania italiana para filhos vale a pena",
        ],
    },
    {
        "topic": "cidadania italiana traducao juramentada",
        "cluster": "documents",
        "intent": "documents",
        "priority_base": 88,
        "patterns": [
            "cidadania italiana traducao juramentada como funciona",
            "cidadania italiana traducao juramentada demora quanto tempo",
            "cidadania italiana traducao juramentada precisa apostilar",
            "cidadania italiana traducao juramentada vale a pena",
            "cidadania italiana traducao juramentada no brasil como funciona",
        ],
    },
    {
        "topic": "cidadania italiana apostilamento de haia",
        "cluster": "documents",
        "intent": "documents",
        "priority_base": 88,
        "patterns": [
            "cidadania italiana apostilamento de haia como funciona",
            "cidadania italiana apostilamento de haia demora quanto tempo",
            "cidadania italiana apostilamento de haia no brasil como funciona",
            "cidadania italiana apostilamento de haia precisa de traducao",
            "cidadania italiana apostilamento de haia vale a pena",
        ],
    },
    {
        "topic": "cidadania italiana nome errado na certidao",
        "cluster": "documents",
        "intent": "documents",
        "priority_base": 86,
        "patterns": [
            "cidadania italiana nome errado na certidao como funciona",
            "cidadania italiana nome errado na certidao como resolver",
            "cidadania italiana nome errado na certidao precisa retificar",
            "cidadania italiana nome errado na certidao demora quanto tempo",
            "cidadania italiana nome errado na certidao atrapalha o processo",
        ],
    },
    {
        "topic": "cidadania italiana via judicial",
        "cluster": "process",
        "intent": "commercial",
        "priority_base": 84,
        "patterns": [
            "cidadania italiana via judicial vale a pena",
            "cidadania italiana via judicial demora quanto tempo",
            "cidadania italiana via judicial como funciona",
            "cidadania italiana via judicial quanto custa",
            "cidadania italiana via judicial precisa de advogado",
        ],
    },
    {
        "topic": "como saber se tenho direito a cidadania italiana",
        "cluster": "eligibility",
        "intent": "qualification",
        "priority_base": 85,
        "patterns": [
            "como saber se tenho direito a cidadania italiana pelo sobrenome",
            "como saber se tenho direito a cidadania italiana com poucos documentos",
            "como saber se tenho direito a cidadania italiana pela linha materna",
            "como saber se tenho direito a cidadania italiana para filhos",
            "como saber se tenho direito a cidadania italiana antes de investir",
        ],
    },
    {
        "topic": "cidadania italiana consulado",
        "cluster": "process",
        "intent": "process",
        "priority_base": 78,
        "patterns": [
            "cidadania italiana consulado demora quanto tempo",
            "cidadania italiana consulado como funciona",
            "cidadania italiana consulado precisa de traducao",
            "cidadania italiana consulado vale a pena",
            "cidadania italiana consulado no brasil como funciona",
        ],
    },
]

STOPWORDS = {
    "a", "o", "e", "de", "da", "do", "das", "dos", "na", "no", "nas", "nos",
    "para", "com", "como", "se", "em", "por", "quanto", "tempo", "que", "ao",
    "à", "as", "os", "um", "uma"
}

BAD_TERMS = {
    "gratis", "grátis", "youtube", "tiktok", "pdf", "download", "wikipedia",
    "telefone", "whatsapp", "reclame", "review", "cupom", "desconto", "curso"
}


# ----------------------------
# HELPERS
# ----------------------------

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


def is_near_duplicate(candidate: str, existing_keywords: set[str]) -> bool:
    cand_norm = normalize(candidate)
    cand_tokens = keyword_tokens(candidate)

    for existing in existing_keywords:
        ex_norm = normalize(existing)
        ex_tokens = keyword_tokens(existing)

        # repetição exata
        if cand_norm == ex_norm:
            return True

        # slug igual
        if slugify(cand_norm) == slugify(ex_norm):
            return True

        # token overlap muito alto
        if cand_tokens and ex_tokens:
            intersection = len(cand_tokens & ex_tokens)
            union = len(cand_tokens | ex_tokens)
            similarity = intersection / union if union else 0

            if similarity >= 0.82:
                return True

        # contém quase tudo do outro
        if cand_tokens and ex_tokens:
            smaller = min(len(cand_tokens), len(ex_tokens))
            common = len(cand_tokens & ex_tokens)
            if smaller > 0 and common / smaller >= 0.9:
                return True

    return False


def has_bad_term(keyword: str) -> bool:
    kw = normalize(keyword)
    return any(term in kw for term in BAD_TERMS)


def looks_like_real_search(keyword: str) -> bool:
    kw = normalize(keyword)

    if len(kw.split()) < 5:
        return False

    if "cidadania italiana" not in kw and "dupla cidadania italiana" not in kw:
        return False

    if has_bad_term(kw):
        return False

    if "vale a pena vale a pena" in kw:
        return False

    if "como funciona como funciona" in kw:
        return False

    if "demora quanto tempo demora quanto tempo" in kw:
        return False

    return True


def detect_intent(keyword: str) -> str:
    kw = normalize(keyword)

    if any(x in kw for x in ["quanto custa", "vale a pena", "precisa de advogado", "investir"]):
        return "commercial"

    if any(x in kw for x in ["documento", "documentos", "certidao", "certidão", "traducao", "tradução", "apostilamento", "apostilar", "retificar"]):
        return "documents"

    if any(x in kw for x in ["como saber se tenho direito", "quem tem direito", "linha materna", "para filhos", "sobrenome"]):
        return "qualification"

    if any(x in kw for x in ["como funciona", "demora quanto tempo", "consulado", "via judicial"]):
        return "process"

    return "informational"


def detect_cluster(keyword: str) -> str:
    kw = normalize(keyword)

    if any(x in kw for x in ["certidao", "certidão", "traducao", "tradução", "apostilamento", "apostilar", "retificar", "documentos"]):
        return "documents"

    if any(x in kw for x in ["linha materna", "para filhos", "sobrenome", "direito"]):
        return "eligibility"

    if any(x in kw for x in ["quanto custa", "vale a pena", "precisa de advogado", "investir"]):
        return "cost"

    if any(x in kw for x in ["como funciona", "demora quanto tempo", "consulado", "via judicial"]):
        return "process"

    return "general"


def score_keyword(keyword: str) -> int:
    kw = normalize(keyword)
    score = 0

    if "cidadania italiana" in kw:
        score += 25

    if any(x in kw for x in ["linha materna", "para filhos", "direito", "sobrenome"]):
        score += 20

    if any(x in kw for x in ["certidao", "certidão", "traducao", "tradução", "apostilamento", "retificar", "documentos"]):
        score += 18

    if any(x in kw for x in ["como funciona", "demora quanto tempo", "via judicial", "consulado"]):
        score += 18

    if any(x in kw for x in ["quanto custa", "vale a pena", "precisa de advogado", "investir"]):
        score += 16

    if 5 <= len(kw.split()) <= 9:
        score += 8

    return min(score, 99)


def priority_from_score(score: int) -> str:
    if score >= 80:
        return "P1"
    if score >= 60:
        return "P2"
    return "P3"


def load_used_keywords() -> set[str]:
    used = set()

    if os.path.exists(USED_KEYWORDS_PATH):
        with open(USED_KEYWORDS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                kw = normalize(line.strip())
                if kw:
                    used.add(kw)

    if os.path.exists(KEYWORDS_MAP_PATH):
        with open(KEYWORDS_MAP_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                kw = normalize((row.get("keyword") or "").strip())
                if kw:
                    used.add(kw)

    return used


def build_candidate_pool() -> list[dict]:
    candidates = []

    for item in PRIMARY_TOPICS:
        base_intent = item["intent"]
        base_cluster = item["cluster"]
        base_priority = item["priority_base"]

        for pattern in item["patterns"]:
            kw = normalize(pattern)

            if not looks_like_real_search(kw):
                continue

            score = max(score_keyword(kw), base_priority)
            intent = detect_intent(kw)
            cluster = detect_cluster(kw)
            priority = priority_from_score(score)

            candidates.append(
                {
                    "keyword": kw,
                    "slug": slugify(kw),
                    "intent": intent if intent != "informational" else base_intent,
                    "cluster": cluster if cluster != "general" else base_cluster,
                    "priority": priority,
                    "score": score,
                }
            )

    # remove duplicados internos
    unique = {}
    for row in candidates:
        unique[row["keyword"]] = row

    return list(unique.values())


def select_daily_keywords(pool: list[dict], used_keywords: set[str], target: int = DAILY_TARGET) -> list[dict]:
    # ordena por score desc
    pool = sorted(pool, key=lambda x: (-int(x["score"]), x["keyword"]))

    selected = []
    temp_seen = set(used_keywords)

    # diversidade de cluster/intenção ajuda SEO do lote
    used_clusters = set()
    used_intents = set()

    # 1ª passada: busca diversidade
    for row in pool:
        kw = row["keyword"]

        if is_near_duplicate(kw, temp_seen):
            continue

        cluster = row["cluster"]
        intent = row["intent"]

        if cluster in used_clusters and intent in used_intents and len(selected) < target - 1:
            continue

        selected.append(row)
        temp_seen.add(kw)
        used_clusters.add(cluster)
        used_intents.add(intent)

        if len(selected) == target:
            return selected

    # 2ª passada: completa o lote sem repetir
    for row in pool:
        kw = row["keyword"]

        if len(selected) == target:
            break

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
            writer.writerow(
                {
                    "date": today,
                    "keyword": row["keyword"],
                    "slug": row["slug"],
                    "intent": row["intent"],
                    "cluster": row["cluster"],
                    "priority": row["priority"],
                    "score": row["score"],
                }
            )


def print_summary(rows: list[dict]) -> None:
    print("\n5 keywords geradas com sucesso:\n")
    for i, row in enumerate(rows, start=1):
        print(f"{i}. {row['keyword']} | intent={row['intent']} | cluster={row['cluster']} | priority={row['priority']} | score={row['score']}")

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