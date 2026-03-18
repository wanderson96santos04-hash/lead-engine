import csv
import html
import os
import re
import unicodedata
from textwrap import dedent

KEYWORDS_MAP_FILE = "../data/keywords_map.csv"
OUTPUT_DIR = "../articles"


# WHITELIST FINAL: só gera artigos destes padrões
APPROVED_KEYWORDS = {
    "cidadania italiana quanto custa",
    "cidadania italiana via judicial quanto custa",
    "como tirar cidadania italiana quanto custa",
    "como tirar cidadania italiana quais documentos",
    "como tirar cidadania italiana sem documentos",
    "documentos cidadania italiana como funciona",
    "documentos cidadania italiana demora quanto tempo",
    "documentos cidadania italiana no brasil",
    "documentos cidadania italiana via judicial",
    "documentos para cidadania italiana via judicial",
    "quanto custa cidadania italiana por descendência",
    "tirar cidadania italiana quanto custa",
    "cidadania italiana quem tem direito",
}


BASE_CSS = """
:root{
  --green:#1F7A4C;
  --green-dark:#17603b;
  --red:#C62828;
  --red-dark:#a61f1f;
  --white:#FFFFFF;
  --off-white:#F5F7FA;
  --text:#1F2933;
  --text-soft:#52606D;
  --line:#D9E2EC;
}
*{box-sizing:border-box}
body{
  margin:0;
  font-family:Inter,Arial,sans-serif;
  color:var(--text);
  background:#fff;
  line-height:1.7;
}
.container{
  width:100%;
  max-width:900px;
  margin:0 auto;
  padding:0 20px;
}
header{
  background:var(--green);
  color:#fff;
  padding:18px 0;
}
.header-inner{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:16px;
}
.brand{
  font-family:"Playfair Display",serif;
  font-size:28px;
  font-weight:700;
}
.brand span{
  display:block;
  font-family:Inter,Arial,sans-serif;
  font-size:13px;
  font-weight:600;
  opacity:.9;
}
.header-cta{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-height:46px;
  padding:0 18px;
  border-radius:12px;
  background:var(--red);
  color:#fff;
  text-decoration:none;
  font-weight:700;
}
.hero{
  padding:46px 0 20px;
}
.breadcrumb{
  font-size:14px;
  color:var(--text-soft);
  margin-bottom:14px;
}
.breadcrumb a{
  color:var(--green);
  text-decoration:none;
}
h1{
  font-family:"Playfair Display",serif;
  font-size:46px;
  line-height:1.1;
  margin:0 0 18px;
}
.lead{
  font-size:20px;
  color:var(--text-soft);
  margin:0 0 22px;
}
.meta{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin-bottom:10px;
}
.meta span{
  background:var(--off-white);
  border:1px solid var(--line);
  border-radius:999px;
  padding:8px 12px;
  font-size:13px;
  font-weight:700;
  color:var(--text);
}
article{
  padding:12px 0 60px;
}
article h2{
  font-family:"Playfair Display",serif;
  font-size:34px;
  line-height:1.2;
  margin:34px 0 14px;
}
article h3{
  font-size:22px;
  line-height:1.3;
  margin:24px 0 10px;
}
article p{
  font-size:18px;
  margin:0 0 16px;
}
article ul{
  margin:0 0 18px 22px;
  padding:0;
}
article li{
  font-size:18px;
  margin-bottom:10px;
}
.notice-box,
.cta-box,
.faq-box{
  border:1px solid var(--line);
  border-radius:20px;
  padding:24px;
  background:var(--off-white);
  margin:28px 0;
}
.notice-box{
  background:#f8fbf9;
  border-color:#d6eadf;
}
.cta-box{
  background:linear-gradient(180deg,#fff 0%,#f8fbf9 100%);
}
.cta-box h2,
.faq-box h2{
  margin-top:0;
}
.cta-btn{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-height:54px;
  padding:0 22px;
  border-radius:12px;
  background:var(--red);
  color:#fff;
  font-weight:800;
  text-decoration:none;
}
.related-links{
  display:grid;
  gap:12px;
}
.related-links a{
  display:block;
  padding:14px 16px;
  border:1px solid var(--line);
  border-radius:14px;
  text-decoration:none;
  color:var(--green-dark);
  font-weight:700;
  background:#fff;
}
footer{
  border-top:1px solid var(--line);
  padding:28px 0 40px;
  color:var(--text-soft);
  font-size:14px;
}
@media (max-width: 640px){
  h1{font-size:34px}
  .lead, article p, article li{font-size:17px}
  article h2{font-size:28px}
  article h3{font-size:20px}
  .header-inner{flex-direction:column;align-items:flex-start}
  .header-cta{width:100%}
}
"""

FAQ_BY_CLUSTER = {
    "eligibility": [
        ("Ter sobrenome italiano garante o direito à cidadania?", "Não. O sobrenome pode ser apenas um indício. O direito depende da linha familiar e da documentação."),
        ("Bisavô italiano ainda pode gerar direito?", "Em muitos casos, sim. Tudo depende da linha de transmissão e do histórico documental."),
        ("Quem não tem documentos perde o direito?", "Não necessariamente. A falta de documentos não elimina automaticamente a possibilidade, mas exige análise mais cuidadosa."),
    ],
    "documents": [
        ("Quais documentos costumam ser mais importantes?", "Normalmente entram certidões de nascimento, casamento e óbito da linha familiar, além de registros italianos quando disponíveis."),
        ("Certidão em inteiro teor é obrigatória?", "Em muitos casos, sim. Isso depende da etapa do processo e da exigência do órgão responsável."),
        ("Erro de nome em documento atrapalha?", "Pode atrapalhar bastante. Divergências em nomes, datas e sobrenomes precisam ser avaliadas com atenção."),
    ],
    "process": [
        ("É melhor fazer no Brasil ou na Itália?", "Depende do perfil do caso, da urgência, da documentação disponível e da estratégia adotada."),
        ("Quanto tempo pode demorar?", "O prazo varia conforme a via escolhida, a qualidade dos documentos e a fila do órgão responsável."),
        ("Dá para começar sem ter tudo pronto?", "Sim. Muitas vezes a triagem inicial serve justamente para organizar o que falta."),
    ],
    "cost": [
        ("Quanto custa tirar cidadania italiana?", "O custo depende da complexidade do caso, das certidões, traduções, retificações e da via escolhida."),
        ("Vale a pena pagar por análise antes?", "Uma boa análise reduz erros, organiza o processo e evita investimento mal feito."),
        ("Processo judicial é sempre mais caro?", "Nem sempre. O custo depende da estratégia e da situação concreta do caso."),
    ],
    "general": [
        ("Como saber se meu caso vale a pena analisar?", "O melhor caminho é uma triagem inicial com perguntas objetivas sobre descendência, documentos e histórico familiar."),
        ("Toda família com origem italiana tem direito?", "Nem sempre. É necessário avaliar a linha de transmissão e a documentação."),
        ("A análise inicial é importante?", "Sim. Ela reduz erros, organiza os próximos passos e ajuda a medir o potencial real do caso."),
    ],
}

RELATED_BY_CLUSTER = {
    "eligibility": [
        "quem tem direito à cidadania italiana",
        "sobrenome italiano ajuda na cidadania",
        "cidadania italiana por descendência",
    ],
    "documents": [
        "documentos para cidadania italiana",
        "certidões para cidadania italiana",
        "retificação de documentos cidadania italiana",
    ],
    "process": [
        "como tirar cidadania italiana",
        "cidadania italiana no brasil",
        "cidadania italiana na itália",
    ],
    "cost": [
        "quanto custa cidadania italiana",
        "vale a pena tirar cidadania italiana",
        "cidadania italiana via judicial",
    ],
    "general": [
        "cidadania italiana",
        "como funciona cidadania italiana",
        "quem tem direito cidadania italiana",
    ],
}


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text)
    return text


def slugify(text: str) -> str:
    text = normalize_text(text)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def escape(text: str) -> str:
    return html.escape(text, quote=True)


def human_title(keyword: str) -> str:
    keyword = keyword.strip()
    if not keyword:
        return "Cidadania Italiana"
    return keyword[0].upper() + keyword[1:]


def is_whitelisted_keyword(keyword: str) -> bool:
    return normalize_text(keyword) in {normalize_text(k) for k in APPROVED_KEYWORDS}


def build_seo_title(keyword: str, intent: str) -> str:
    title = human_title(keyword)

    if intent == "commercial":
        return f"{title}: custos, cenário e como avaliar"
    if intent == "documents":
        return f"{title}: quais documentos analisar e por onde começar"
    if intent == "process":
        return f"{title}: como funciona na prática"
    if intent == "qualification":
        return f"{title}: o que avaliar no seu caso"
    return f"{title}: guia completo e atualizado"


def build_meta_description(keyword: str, cluster: str) -> str:
    base = (
        f"Entenda {keyword}, veja pontos essenciais, erros comuns e descubra "
        "quando vale a pena fazer uma análise gratuita do seu caso."
    )
    if cluster == "cost":
        base = (
            f"Saiba como avaliar {keyword}, o que influencia custo, prazo e "
            "viabilidade antes de iniciar o processo."
        )
    elif cluster == "documents":
        base = (
            f"Entenda {keyword}, os documentos mais importantes, erros comuns e "
            "o que observar antes da análise."
        )
    return base[:155]


def intro_paragraphs(keyword: str, cluster: str) -> list[str]:
    intros = {
        "eligibility": [
            f"Quem pesquisa sobre {keyword} normalmente quer descobrir se existe uma chance real de reconhecimento da cidadania italiana dentro da própria família.",
            "Essa dúvida é comum porque muitas famílias brasileiras conhecem sua origem italiana, mas não sabem se isso se transforma em um caso viável na prática.",
            "Antes de pensar em custos ou prazos, a prioridade é entender elegibilidade, linha familiar e força documental."
        ],
        "documents": [
            f"Quem procura por {keyword} geralmente já percebeu que a documentação é uma das partes mais importantes da cidadania italiana.",
            "Na prática, o problema não é apenas reunir papéis. O ponto central é saber quais documentos realmente fazem diferença e quais erros podem travar o caso.",
            "Uma triagem bem feita nessa fase economiza tempo, reduz retrabalho e melhora muito a qualidade da decisão."
        ],
        "process": [
            f"Buscar por {keyword} mostra uma intenção clara de entender como o processo funciona fora da teoria.",
            "O caminho para a cidadania italiana muda conforme a documentação, a linha familiar e a estratégia adotada.",
            "Por isso, compreender a lógica do processo antes de começar evita atrasos e decisões ruins."
        ],
        "cost": [
            f"Quando a busca é por {keyword}, o interesse normalmente está mais próximo da decisão do que da simples curiosidade.",
            "O custo da cidadania italiana não depende só de preço inicial. Ele varia conforme complexidade documental, urgência e estratégia.",
            "Avaliar investimento sem olhar viabilidade quase sempre gera expectativa errada."
        ],
        "general": [
            f"{human_title(keyword)} é um tema que mistura origem familiar, documentação e estratégia.",
            "Na prática, os melhores resultados aparecem quando a pessoa entende seu caso por etapas: elegibilidade, documentos, caminho possível e próximos passos.",
            "Esse conteúdo foi estruturado para responder exatamente essas dúvidas de forma útil e direta."
        ],
    }
    return intros.get(cluster, intros["general"])


def section_what_it_means(cluster: str) -> str:
    mapping = {
        "eligibility": "No contexto da cidadania italiana, esse tipo de busca normalmente indica que a pessoa quer confirmar se a linha familiar tem potencial real. O foco está em descendência, transmissão e documentação mínima.",
        "documents": "Nesse cenário, a pessoa já saiu da curiosidade inicial e percebeu que a força documental muda completamente o rumo do caso.",
        "process": "Aqui a intenção é entender o caminho real para avançar, incluindo etapas, obstáculos e organização prévia.",
        "cost": "Nesse tipo de busca, a pessoa quer avaliar investimento e retorno. O mais importante é perceber que custo e viabilidade precisam andar juntos.",
        "general": "Esse tipo de busca mistura várias dúvidas ao mesmo tempo. Entender o real significado do tema ajuda a filtrar expectativa e priorizar o que analisar primeiro.",
    }
    return mapping.get(cluster, mapping["general"])


def section_key_points(cluster: str) -> list[str]:
    mapping = {
        "eligibility": [
            "identificar o ancestral italiano e a linha de transmissão",
            "verificar se a família tem dados mínimos para pesquisa",
            "avaliar se existem documentos ou pistas relevantes",
            "entender se o caso merece uma análise mais aprofundada",
        ],
        "documents": [
            "mapear quais certidões já existem e quais faltam",
            "identificar divergências de nomes, datas e sobrenomes",
            "entender quais documentos realmente destravam a análise",
            "evitar iniciar o processo com base documental fraca",
        ],
        "process": [
            "entender as etapas antes de investir tempo e dinheiro",
            "separar triagem, organização documental e execução",
            "escolher a via mais coerente com o perfil do caso",
            "reduzir retrabalho com um plano claro",
        ],
        "cost": [
            "avaliar custo junto com complexidade documental",
            "entender impacto de buscas, traduções e retificações",
            "comparar investimento com chance real de avanço",
            "evitar decisão baseada apenas em promessa comercial",
        ],
        "general": [
            "entender se existe base familiar para análise",
            "identificar os documentos mais importantes",
            "avaliar qual caminho faz mais sentido",
            "transformar curiosidade em decisão com segurança",
        ],
    }
    return mapping.get(cluster, mapping["general"])


def section_common_mistakes(cluster: str) -> list[str]:
    mapping = {
        "eligibility": [
            "achar que sobrenome sozinho garante direito",
            "presumir que toda descendência italiana é automaticamente viável",
            "começar sem organizar dados básicos da família",
        ],
        "documents": [
            "juntar certidões sem validar coerência entre elas",
            "ignorar erros pequenos em nomes e datas",
            "usar documentação antiga sem confirmação oficial",
        ],
        "process": [
            "iniciar o processo sem roteiro claro",
            "escolher caminho pela pressa e não pela estratégia",
            "subestimar a preparação documental",
        ],
        "cost": [
            "comparar apenas o menor preço",
            "avaliar custo sem medir risco de retrabalho",
            "confundir orçamento inicial com custo total",
        ],
        "general": [
            "tentar resolver tudo de uma vez sem triagem",
            "consumir apenas conteúdo superficial",
            "avançar sem medir se o caso é viável",
        ],
    }
    return mapping.get(cluster, mapping["general"])


def section_next_step(cluster: str) -> str:
    mapping = {
        "eligibility": "O próximo passo mais inteligente é fazer uma triagem objetiva com perguntas sobre ancestral italiano, documentos disponíveis e histórico familiar.",
        "documents": "Antes de pedir certidões aleatórias, vale organizar uma visão clara do que existe, do que falta e do que realmente será relevante.",
        "process": "Se a intenção é avançar, o melhor caminho é começar por uma análise inicial. Com isso, fica mais fácil decidir a rota certa.",
        "cost": "A decisão mais segura é analisar viabilidade e complexidade primeiro. Depois disso, preço deixa de ser chute e vira planejamento.",
        "general": "Em vez de consumir muitos conteúdos soltos, a melhor decisão é concentrar as informações do caso e fazer uma análise inicial objetiva.",
    }
    return mapping.get(cluster, mapping["general"])


def build_faq_html(cluster: str) -> str:
    faqs = FAQ_BY_CLUSTER.get(cluster, FAQ_BY_CLUSTER["general"])
    items = []

    for question, answer in faqs:
        items.append(
            f"""
            <div class="faq-item">
              <h3>{escape(question)}</h3>
              <p>{escape(answer)}</p>
            </div>
            """
        )

    return f"""
    <section class="faq-box">
      <h2>Perguntas frequentes</h2>
      {''.join(items)}
    </section>
    """


def build_related_links(cluster: str, current_keyword: str) -> str:
    related = RELATED_BY_CLUSTER.get(cluster, RELATED_BY_CLUSTER["general"])
    links = []

    for keyword in related:
        if normalize_text(keyword) == normalize_text(current_keyword):
            continue
        slug = slugify(keyword)
        links.append(f'<a href="{slug}.html">{escape(human_title(keyword))}</a>')

    return f"""
    <section>
      <h2>Leituras relacionadas</h2>
      <div class="related-links">
        {''.join(links[:3])}
      </div>
    </section>
    """


def build_article_html(row: dict) -> str:
    keyword = row["keyword"]
    intent = row.get("intent", "informational")
    cluster = row.get("cluster", "general")
    priority = row.get("priority", "P3")

    seo_title = build_seo_title(keyword, intent)
    meta_description = build_meta_description(keyword, cluster)
    title = human_title(keyword)

    intro = intro_paragraphs(keyword, cluster)
    key_points = section_key_points(cluster)
    mistakes = section_common_mistakes(cluster)

    faq_html = build_faq_html(cluster)
    related_html = build_related_links(cluster, keyword)

    list_points_html = "".join([f"<li>{escape(item)}</li>" for item in key_points])
    mistakes_html = "".join([f"<li>{escape(item)}</li>" for item in mistakes])

    article_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(seo_title)}</title>
  <meta name="description" content="{escape(meta_description)}" />
  <meta name="robots" content="index,follow" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700;800&display=swap" rel="stylesheet" />
  <style>{BASE_CSS}</style>
</head>
<body>
  <header>
    <div class="container header-inner">
      <div class="brand">Cidadania Italiana<span>Online</span></div>
      <a class="header-cta" href="/">Fazer análise gratuita</a>
    </div>
  </header>

  <main class="container">
    <section class="hero">
      <div class="breadcrumb">
        <a href="/">Início</a> / <span>{escape(title)}</span>
      </div>

      <h1>{escape(title)}</h1>

      <p class="lead">
        Entenda os pontos centrais sobre {escape(keyword)}, evite erros comuns e descubra
        quando vale a pena fazer uma análise inicial do seu caso.
      </p>

      <div class="meta">
        <span>Intenção: {escape(intent)}</span>
        <span>Cluster: {escape(cluster)}</span>
        <span>Prioridade: {escape(priority)}</span>
      </div>
    </section>

    <article>
      <p>{escape(intro[0])}</p>
      <p>{escape(intro[1])}</p>
      <p>{escape(intro[2])}</p>

      <div class="notice-box">
        <h2>Resumo rápido</h2>
        <p>
          Antes de avançar com qualquer expectativa sobre cidadania italiana, o mais seguro é
          validar elegibilidade, documentos e caminho possível. Isso reduz erro, retrabalho e
          melhora a qualidade da decisão.
        </p>
      </div>

      <h2>O que essa busca realmente significa</h2>
      <p>{escape(section_what_it_means(cluster))}</p>
      <p>
        Em projetos sérios de cidadania, informação isolada raramente resolve. O ganho real
        acontece quando a pessoa entende onde está no processo e qual dado precisa validar primeiro.
      </p>

      <h2>O que analisar primeiro</h2>
      <p>
        Para transformar interesse em ação concreta, estes pontos costumam vir antes de qualquer decisão maior:
      </p>
      <ul>
        {list_points_html}
      </ul>

      <h2>Erros mais comuns nesse tipo de caso</h2>
      <p>
        Muitos processos travam não por falta total de chance, mas por decisões erradas tomadas cedo demais.
      </p>
      <ul>
        {mistakes_html}
      </ul>

      <h2>Como pensar no próximo passo</h2>
      <p>{escape(section_next_step(cluster))}</p>
      <p>
        Em vez de tentar resolver tudo sozinho de uma vez, a abordagem mais eficiente é reunir as informações
        essenciais e usar uma triagem inicial para separar curiosidade de oportunidade real.
      </p>

      <div class="cta-box">
        <h2>Descubra se o seu caso pode avançar</h2>
        <p>
          Responda poucas perguntas e veja se existem sinais iniciais de viabilidade para a sua cidadania italiana.
        </p>
        <a class="cta-btn" href="/">COMEÇAR ANÁLISE GRATUITA</a>
      </div>

      {faq_html}

      {related_html}
    </article>
  </main>

  <footer>
    <div class="container">
      Conteúdo informativo com foco em triagem inicial e educação do usuário sobre cidadania italiana.
    </div>
  </footer>
</body>
</html>
"""
    return dedent(article_html)


def load_keywords_map() -> list[dict]:
    if not os.path.exists(KEYWORDS_MAP_FILE):
        raise FileNotFoundError(
            f"Arquivo não encontrado: {KEYWORDS_MAP_FILE}. Gere primeiro o keywords_map.csv."
        )

    rows = []
    with open(KEYWORDS_MAP_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            keyword = (row.get("keyword") or "").strip()
            slug = (row.get("slug") or "").strip()

            if not keyword or not slug:
                continue

            rows.append(
                {
                    "keyword": keyword,
                    "slug": slug,
                    "intent": (row.get("intent") or "informational").strip(),
                    "cluster": (row.get("cluster") or "general").strip(),
                    "priority": (row.get("priority") or "P3").strip(),
                    "score": (row.get("score") or "0").strip(),
                }
            )
    return rows


def clear_existing_articles() -> None:
    if not os.path.exists(OUTPUT_DIR):
        return

    for file_name in os.listdir(OUTPUT_DIR):
        if file_name.endswith(".html"):
            try:
                os.remove(os.path.join(OUTPUT_DIR, file_name))
            except OSError:
                pass


def generate_articles() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    clear_existing_articles()

    keyword_rows = load_keywords_map()

    selected = [
        row for row in keyword_rows
        if is_whitelisted_keyword(row["keyword"])
    ]

    selected.sort(key=lambda row: normalize_text(row["keyword"]))

    if not selected:
        print("Nenhuma keyword aprovada encontrada no keywords_map.csv.")
        return

    for row in selected:
        article_html = build_article_html(row)
        path = os.path.join(OUTPUT_DIR, f'{row["slug"]}.html')

        with open(path, "w", encoding="utf-8") as file:
            file.write(article_html)

        print(
            f'Artigo criado: {path} | '
            f'intent={row["intent"]} | cluster={row["cluster"]} | priority={row["priority"]}'
        )


if __name__ == "__main__":
    generate_articles()