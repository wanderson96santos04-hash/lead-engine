import os
import shutil

ARTICLES_DIR = "../articles"
BLOG_DIR = "../site/blog"

INDEX_FILE = "../site/blog.html"


def publish_articles():

    os.makedirs(BLOG_DIR, exist_ok=True)

    articles = os.listdir(ARTICLES_DIR)

    links = []

    for article in articles:

        src = os.path.join(ARTICLES_DIR, article)
        dst = os.path.join(BLOG_DIR, article)

        shutil.copy(src, dst)

        title = article.replace("-", " ").replace(".html", "").capitalize()

        link = f'<li><a href="blog/{article}">{title}</a></li>'

        links.append(link)

        print(f"Publicado: {article}")

    create_blog_index(links)


def create_blog_index(links):

    html = f"""
    <html>

    <head>
    <title>Blog - Cidadania Italiana Online</title>
    </head>

    <body>

    <h1>Blog sobre Cidadania Italiana</h1>

    <ul>

    {''.join(links)}

    </ul>

    </body>

    </html>
    """

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print("Página do blog criada.")


if __name__ == "__main__":
    publish_articles()