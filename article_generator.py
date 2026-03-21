import csv
import html
import json
import os
import re
import unicodedata
from textwrap import dedent

KEYWORDS_MAP_FILE = "../data/keywords_map.csv"
OUTPUT_DIR = "../articles"
SITE_URL = "https://analisecidadaniaitaliana.com/artigos"


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
article a{
  color:var(--green);
  text-decoration:none;
  font-weight:600;
}
article a:hover{
  text-decoration:underline;
}
.notice-box,
.cta-box,
.faq-box,
.lead-box{
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
.cta-box,
.lead-box{
  background:linear-gradient(180deg,#fff 0%,#f8fbf9 100%);
}
.cta-box h2,
.faq-box h2,
.lead-box h2,
.lead-box h3{
  margin-top:0;
}
.cta-btn,
.lead-btn{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-height:54px;
  padding:0 22px;
  border-radius:12px;
  background:var(--red);
  color:#fff !important;
  font-weight:800;
  text-decoration:none;
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
  .cta-btn,.lead-btn{width:100%}
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


def is_valid_keyword_row(row: dict) -> bool:
    keyword = normalize_text(row.get("keyword", ""))
    slug = (row.get("slug") or "").strip()
    intent = (row.get("intent") or "").strip()
    cluster = (row.get("cluster") or "").strip()
    priority = (row.get("priority") or "").strip()

    if not keyword or not slug:
        return False

    if len(keyword) < 10:
        return False

    allowed_intents = {"commercial", "documents", "process", "qualification", "informational"}
    allowed_clusters = {"eligibility", "documents", "process", "cost", "general", "local"}

    if intent not in allowed_intents:
        return False

    if cluster not in allowed_clusters:
        return False

    if priority not in {"P1", "P2", "P3"}:
        return False

    return True


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
    if cluster == "cost":
        text = f"Saiba como avaliar {keyword}, o que influencia custo, prazo e viabilidade antes de iniciar o processo de cidadania italiana."
    elif cluster == "documents":
        text = f"Entenda {keyword}, veja os documentos mais importantes, erros comuns e o que observar antes de começar a análise."
    elif cluster == "eligibility":
        text = f"Descubra como avaliar {keyword}, quais sinais merecem atenção e quando vale a pena fazer uma análise inicial do caso."
    else:
        text = f"Entenda {keyword}, veja pontos essenciais, erros comuns e descubra quando vale a pena analisar seu caso."
    return text[:155]


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


def build_lead_block_middle(cluster: str) -> str:
    titles = {
        "cost": "Descubra o custo real do seu caso",
        "documents": "Veja se sua documentação tem potencial",
        "eligibility": "Descubra se o seu caso pode ter direito",
        "process": "Entenda qual caminho faz mais sentido",
        "general": "Receba uma análise inicial gratuita",
    }

    descriptions = {
        "cost": "Cada processo tem um custo diferente. O valor real depende da sua documentação, da linha familiar e da estratégia mais adequada.",
        "documents": "Antes de gastar com certidões e retificações, vale entender se os seus documentos já mostram um bom potencial de avanço.",
        "eligibility": "Ter sobrenome italiano ou origem familiar não basta sozinho. Uma análise inicial ajuda a separar curiosidade de oportunidade real.",
        "process": "Nem todo caso deve seguir o mesmo caminho. Uma triagem inicial ajuda a evitar erros e economiza tempo.",
        "general": "Uma análise inicial gratuita ajuda a identificar os próximos passos mais inteligentes para o seu caso.",
    }

    title = titles.get(cluster, titles["general"])
    description = descriptions.get(cluster, descriptions["general"])

    return f"""
    <div class="lead-box">
      <h3>{escape(title)}</h3>
      <p>{escape(description)}</p>
      <p><strong>Evite perder tempo e dinheiro com decisões feitas no escuro.</strong></p>
      <a class="lead-btn" href="/#quiz">Descobrir se tenho direito à cidadania italiana (grátis)</a>
    </div>
    """


def build_lead_block_final(cluster: str) -> str:
    titles = {
        "cost": "Antes de decidir pelo preço",
        "documents": "Antes de sair pedindo documentos",
        "eligibility": "Antes de concluir que tem ou não direito",
        "process": "Antes de escolher o caminho do processo",
        "general": "Antes de tomar qualquer decisão",
    }

    descriptions = {
        "cost": "O erro mais comum é comparar valores sem analisar viabilidade. O custo certo só faz sentido quando o caso também tem chance real de avanço.",
        "documents": "O erro mais comum é gastar com papéis sem saber o que realmente importa para a análise do caso.",
        "eligibility": "O erro mais comum é confiar em sinais isolados e ignorar a força real da linha familiar e da documentação.",
        "process": "O erro mais comum é seguir por pressa, sem avaliar qual estratégia é mais coerente com a realidade do caso.",
        "general": "Uma análise inicial pode evitar retrabalho, reduzir erros e mostrar com mais clareza o melhor próximo passo.",
    }

    title = titles.get(cluster, titles["general"])
    description = descriptions.get(cluster, descriptions["general"])

    return f"""
    <div class="lead-box">
      <h2>{escape(title)}</h2>
      <p>{escape(description)}</p>
      <p>Responda poucas perguntas e receba uma triagem inicial gratuita para entender se vale a pena aprofundar o seu caso.</p>
      <a class="lead-btn" href="/#quiz">Descobrir se tenho direito à cidadania italiana (grátis)</a>
    </div>
    """


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


def build_faq_schema(cluster: str) -> str:
    faqs = FAQ_BY_CLUSTER.get(cluster, FAQ_BY_CLUSTER["general"])
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": a
                }
            }
            for q, a in faqs
        ]
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def build_article_schema(title: str, seo_title: str, meta_description: str, canonical_url: str) -> str:
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": seo_title,
        "name": title,
        "description": meta_description,
        "mainEntityOfPage": canonical_url,
        "author": {
            "@type": "Organization",
            "name": "Cidadania Italiana Online"
        },
        "publisher": {
            "@type": "Organization",
            "name": "Cidadania Italiana Online"
        }
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


def build_related_articles_html(current_row: dict, all_rows: list[dict], limit: int = 3) -> str:
    related = []

    current_slug = current_row["slug"]
    current_cluster = current_row.get("cluster", "general")

    same_cluster = [
        row for row in all_rows
        if row["slug"] != current_slug and row.get("cluster", "general") == current_cluster
    ]

    other_cluster = [
        row for row in all_rows
        if row["slug"] != current_slug and row.get("cluster", "general") != current_cluster
    ]

    ordered = same_cluster + other_cluster

    seen = set()
    for row in ordered:
        if row["slug"] not in seen:
            seen.add(row["slug"])
            related.append(row)
        if len(related) >= limit:
            break

    if not related:
        return ""

    items = []
    for row in related:
        items.append(
            f'<li><a href="{escape(row["slug"])}.html">{escape(human_title(row["keyword"]))}</a></li>'
        )

    return f"""
    <section class="notice-box">
      <h2>Leia também</h2>
      <p>Veja outros conteúdos relacionados que podem ajudar na sua análise inicial:</p>
      <ul>
        {''.join(items)}
      </ul>
    </section>
    """


def build_articles_index(rows: list[dict]) -> str:
    cards = []

    for row in rows:
        title = human_title(row["keyword"])
        slug = row["slug"]
        intent = row.get("intent", "informational")
        cluster = row.get("cluster", "general")

        cards.append(f"""
        <a class="article-card" href="{escape(slug)}.html">
          <h2>{escape(title)}</h2>
          <p>Conteúdo informativo sobre {escape(row["keyword"])} com foco em triagem inicial e geração de leads qualificados.</p>
          <div class="card-meta">
            <span>{escape(intent)}</span>
            <span>{escape(cluster)}</span>
          </div>
        </a>
        """)

    index_css = """
    :root{
      --green:#1F7A4C;
      --green-dark:#17603b;
      --red:#C62828;
      --off-white:#F5F7FA;
      --text:#1F2933;
      --text-soft:#52606D;
      --line:#D9E2EC;
      --white:#FFFFFF;
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
      max-width:1100px;
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
    main{
      padding:42px 0 60px;
    }
    h1{
      font-family:"Playfair Display",serif;
      font-size:44px;
      line-height:1.1;
      margin:0 0 14px;
    }
    .lead{
      font-size:20px;
      color:var(--text-soft);
      margin:0 0 28px;
      max-width:850px;
    }
    .articles-grid{
      display:grid;
      grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
      gap:18px;
    }
    .article-card{
      display:block;
      text-decoration:none;
      color:inherit;
      border:1px solid var(--line);
      border-radius:18px;
      padding:22px;
      background:var(--off-white);
      transition:.2s ease;
    }
    .article-card:hover{
      transform:translateY(-2px);
      border-color:#bfd3c7;
    }
    .article-card h2{
      font-size:24px;
      line-height:1.25;
      margin:0 0 10px;
      font-family:"Playfair Display",serif;
      color:var(--text);
    }
    .article-card p{
      margin:0 0 14px;
      font-size:16px;
      color:var(--text-soft);
    }
    .card-meta{
      display:flex;
      flex-wrap:wrap;
      gap:8px;
    }
    .card-meta span{
      background:#fff;
      border:1px solid var(--line);
      border-radius:999px;
      padding:6px 10px;
      font-size:12px;
      font-weight:700;
      color:var(--text);
    }
    footer{
      border-top:1px solid var(--line);
      padding:28px 0 40px;
      color:var(--text-soft);
      font-size:14px;
    }
    @media (max-width: 640px){
      h1{font-size:34px}
      .lead{font-size:18px}
      .header-inner{flex-direction:column;align-items:flex-start}
      .header-cta{width:100%}
    }
    """

    index_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Artigos sobre cidadania italiana</title>
  <meta name="description" content="Página de artigos sobre cidadania italiana com foco em dúvidas comuns, documentos, custos e análise inicial." />
  <meta name="robots" content="index,follow" />
  <link rel="canonical" href="{SITE_URL}/index.html" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700;800&display=swap" rel="stylesheet" />
  <style>{index_css}</style>
</head>
<body>
  <header>
    <div class="container header-inner">
      <div class="brand">Cidadania Italiana<span>Online</span></div>
      <a class="header-cta" href="https://analisecidadaniaitaliana.com/#quiz">Descobrir se tenho direito à cidadania italiana (grátis)</a>
    </div>
  </header>

  <main class="container">
    <h1>Artigos sobre cidadania italiana</h1>
    <p class="lead">
      Conteúdos informativos para ajudar na triagem inicial, esclarecer dúvidas frequentes e gerar leads qualificados.
    </p>

    <section class="articles-grid">
      {''.join(cards)}
    </section>
  </main>

  <footer>
    <div class="container">
      Conteúdo informativo com foco em triagem inicial e educação do usuário sobre cidadania italiana.
    </div>
  </footer>
</body>
</html>
"""
    return dedent(index_html)


def build_article_html(row: dict, all_rows: list[dict]) -> str:
    keyword = row["keyword"]
    intent = row.get("intent", "informational")
    cluster = row.get("cluster", "general")
    priority = row.get("priority", "P3")
    slug = row["slug"]

    seo_title = build_seo_title(keyword, intent)
    meta_description = build_meta_description(keyword, cluster)
    title = human_title(keyword)
    canonical_url = f"{SITE_URL}/{slug}.html"

    intro = intro_paragraphs(keyword, cluster)
    key_points = section_key_points(cluster)
    mistakes = section_common_mistakes(cluster)

    faq_html = build_faq_html(cluster)
    faq_schema = build_faq_schema(cluster)
    article_schema = build_article_schema(title, seo_title, meta_description, canonical_url)
    lead_block_middle = build_lead_block_middle(cluster)
    lead_block_final = build_lead_block_final(cluster)
    related_articles_html = build_related_articles_html(row, all_rows)

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
  <link rel="canonical" href="{escape(canonical_url)}" />

  <meta property="og:type" content="article" />
  <meta property="og:title" content="{escape(seo_title)}" />
  <meta property="og:description" content="{escape(meta_description)}" />
  <meta property="og:url" content="{escape(canonical_url)}" />
  <meta property="og:site_name" content="Cidadania Italiana Online" />

  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{escape(seo_title)}" />
  <meta name="twitter:description" content="{escape(meta_description)}" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700;800&display=swap" rel="stylesheet" />
  <style>{BASE_CSS}</style>

  <script type="application/ld+json">
{article_schema}
  </script>
  <script type="application/ld+json">
{faq_schema}
  </script>
</head>
<body>
  <header>
    <div class="container header-inner">
      <div class="brand">Cidadania Italiana<span>Online</span></div>
      <a class="header-cta" href="https://analisecidadaniaitaliana.com/#quiz">Descobrir se tenho direito à cidadania italiana (grátis)</a>
    </div>
  </header>

  <main class="container">
    <section class="hero">
      <div class="breadcrumb">
        <a href="/">Início</a> / <a href="/artigos/index.html">Artigos</a> / <span>{escape(title)}</span>
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

      {lead_block_middle}

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
        <a class="cta-btn" href="https://analisecidadaniaitaliana.com/#quiz">Descobrir se tenho direito à cidadania italiana (grátis)</a>
      </div>

      {related_articles_html}

      {faq_html}

      {lead_block_final}
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

            parsed_row = {
                "keyword": keyword,
                "slug": slugify(slug or keyword),
                "intent": (row.get("intent") or "informational").strip(),
                "cluster": (row.get("cluster") or "general").strip(),
                "priority": (row.get("priority") or "P3").strip(),
                "score": (row.get("score") or "0").strip(),
            }

            if is_valid_keyword_row(parsed_row):
                rows.append(parsed_row)

    return rows


def generate_articles() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    keyword_rows = load_keywords_map()
    selected = sorted(
        keyword_rows,
        key=lambda row: (
            {"P1": 1, "P2": 2, "P3": 3}.get(row["priority"], 9),
            normalize_text(row["keyword"]),
        ),
    )

    if not selected:
        print("Nenhuma keyword aprovada encontrada no keywords_map.csv.")
        return

    generated_rows = []

    for row in selected:
        article_html = build_article_html(row, selected)
        path = os.path.join(OUTPUT_DIR, f'{row["slug"]}.html')

        with open(path, "w", encoding="utf-8") as file:
            file.write(article_html)

        generated_rows.append(row)

        print(
            f'Artigo criado: {path} | '
            f'intent={row["intent"]} | cluster={row["cluster"]} | priority={row["priority"]}'
        )

    index_html = build_articles_index(generated_rows)
    index_path = os.path.join(OUTPUT_DIR, "index.html")

    with open(index_path, "w", encoding="utf-8") as file:
        file.write(index_html)

    print(f"Página de artigos criada: {index_path}")


if __name__ == "__main__":
    generate_articles()