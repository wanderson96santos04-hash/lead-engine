from ftplib import FTP_TLS
import os
import posixpath

FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASSWORD = os.getenv("FTP_PASSWORD")

REMOTE_ARTICLES_DIR = "/public_html/artigos"

def connect():
    ftp = FTP_TLS()
    ftp.connect(FTP_HOST, 21)
    ftp.login(FTP_USER, FTP_PASSWORD)
    ftp.prot_p()
    ftp.encoding = "utf-8"
    print("✅ Conectado")
    return ftp

def delete_all_articles():
    ftp = connect()

    arquivos = []
    ftp.retrlines(f"NLST {REMOTE_ARTICLES_DIR}", arquivos.append)

    for file in arquivos:
        nome = posixpath.basename(file)

        if nome.endswith(".html"):
            try:
                ftp.delete(file)
                print(f"🗑️ Removido: {file}")
            except Exception as e:
                print(f"Erro ao remover {file}: {e}")

    ftp.quit()
    print("✅ Limpeza concluída")

if __name__ == "__main__":
    delete_all_articles()