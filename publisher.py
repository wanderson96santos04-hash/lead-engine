import io
import os
import posixpath
from ftplib import FTP_TLS, error_perm
from xml.sax.saxutils import escape

ARTICLES_DIR = "../articles"
SITE_DOMAIN = "https://analisecidadaniaitaliana.com"
REMOTE_ROOT = "/public_html"
REMOTE_ARTICLES_DIR = f"{REMOTE_ROOT}/artigos"
SITEMAP_REMOTE_PATH = f"{REMOTE_ROOT}/sitemap.xml"
ROBOTS_REMOTE_PATH = f"{REMOTE_ROOT}/robots.txt"

FTP_HOST = os.getenv("FTP_HOST", "").strip()
FTP_USER = os.getenv("FTP_USER", "").strip()
FTP_PASSWORD = os.getenv("FTP_PASSWORD", "").strip()


def require_env() -> None:
    missing = []

    if not FTP_HOST:
        missing.append("FTP_HOST")
    if not FTP_USER:
        missing.append("FTP_USER")
    if not FTP_PASSWORD:
        missing.append("FTP_PASSWORD")

    if missing:
        raise RuntimeError(
            "Variáveis de ambiente ausentes: " + ", ".join(missing)
        )


def connect_ftp() -> FTP_TLS:
    ftp = FTP_TLS(timeout=30)
    ftp.connect(FTP_HOST, 21)
    ftp.login(FTP_USER, FTP_PASSWORD)
    ftp.prot_p()
    ftp.encoding = "utf-8"
    print("✅ Conectado à Hostinger via FTPS")
    return ftp


def ensure_remote_dir(ftp: FTP_TLS, remote_dir: str) -> None:
    parts = [p for p in remote_dir.split("/") if p]
    current = ""

    for part in parts:
        current = f"{current}/{part}"
        try:
            ftp.mkd(current)
            print(f"📁 Pasta criada: {current}")
        except error_perm as e:
            message = str(e).lower()
            if "exist" in message or "file exists" in message:
                pass
            else:
                # pasta já pode existir ou o servidor só recusou mkd por já existir
                pass


def upload_binary_content(ftp: FTP_TLS, content: bytes, remote_path: str) -> None:
    with io.BytesIO(content) as bio:
        ftp.storbinary(f"STOR {remote_path}", bio)
    print(f"⬆️ Enviado: {remote_path}")


def upload_file(ftp: FTP_TLS, local_path: str, remote_path: str) -> None:
    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {remote_path}", f)
    print(f"⬆️ Enviado: {local_path} -> {remote_path}")


def list_local_articles() -> list[str]:
    if not os.path.exists(ARTICLES_DIR):
        raise FileNotFoundError(f"Pasta não encontrada: {ARTICLES_DIR}")

    files = []
    for file_name in os.listdir(ARTICLES_DIR):
        if file_name.lower().endswith(".html"):
            files.append(file_name)

    files.sort()
    return files


def list_remote_articles(ftp: FTP_TLS) -> list[str]:
    remote_files = []

    try:
        entries = []
        ftp.retrlines(f"NLST {REMOTE_ARTICLES_DIR}", entries.append)

        for entry in entries:
            name = posixpath.basename(entry.strip())
            if name.lower().endswith(".html"):
                remote_files.append(name)

    except error_perm:
        # pasta ainda não existe ou está vazia
        return []

    remote_files.sort()
    return remote_files


def delete_remote_missing_articles(ftp: FTP_TLS, local_article_files: list[str]) -> None:
    remote_article_files = list_remote_articles(ftp)
    local_set = set(local_article_files)

    for remote_file in remote_article_files:
        if remote_file not in local_set:
            remote_path = posixpath.join(REMOTE_ARTICLES_DIR, remote_file)
            try:
                ftp.delete(remote_path)
                print(f"🗑️ Removido do servidor: {remote_path}")
            except error_perm as e:
                print(f"⚠️ Não foi possível remover {remote_path}: {e}")


def generate_sitemap(article_files: list[str]) -> str:
    urls = [
        f"{SITE_DOMAIN}/",
    ]

    for file_name in article_files:
        urls.append(f"{SITE_DOMAIN}/artigos/{file_name}")

    url_tags = []
    for url in urls:
        url_tags.append(
            f"""  <url>
    <loc>{escape(url)}</loc>
  </url>"""
        )

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(url_tags)}
</urlset>
"""
    return sitemap


def generate_robots_txt() -> str:
    return f"""User-agent: *
Allow: /

Sitemap: {SITE_DOMAIN}/sitemap.xml
"""


def upload_articles(ftp: FTP_TLS, article_files: list[str]) -> None:
    ensure_remote_dir(ftp, REMOTE_ARTICLES_DIR)

    for file_name in article_files:
        local_path = os.path.join(ARTICLES_DIR, file_name)
        remote_path = posixpath.join(REMOTE_ARTICLES_DIR, file_name)
        upload_file(ftp, local_path, remote_path)


def upload_sitemap(ftp: FTP_TLS, article_files: list[str]) -> None:
    sitemap_content = generate_sitemap(article_files).encode("utf-8")
    upload_binary_content(ftp, sitemap_content, SITEMAP_REMOTE_PATH)
    print("🗺️ sitemap.xml atualizado")


def upload_robots_txt(ftp: FTP_TLS) -> None:
    robots_content = generate_robots_txt().encode("utf-8")
    upload_binary_content(ftp, robots_content, ROBOTS_REMOTE_PATH)
    print("🤖 robots.txt atualizado")


def publish() -> None:
    require_env()

    article_files = list_local_articles()

    if not article_files:
        print("Nenhum artigo encontrado para publicar.")
        return

    print(f"📰 {len(article_files)} artigos encontrados para publicação")

    ftp = connect_ftp()
    try:
        ensure_remote_dir(ftp, REMOTE_ARTICLES_DIR)
        delete_remote_missing_articles(ftp, article_files)
        upload_articles(ftp, article_files)
        upload_sitemap(ftp, article_files)
        upload_robots_txt(ftp)
    finally:
        try:
            ftp.quit()
        except Exception:
            pass
        print("🔒 Conexão encerrada")

    print("✅ Publicação concluída com sucesso")


if __name__ == "__main__":
    publish()