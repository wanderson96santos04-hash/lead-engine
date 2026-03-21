@echo off

echo Configurando credenciais FTP...
set FTP_HOST=46.202.183.214
set FTP_USER=u935013836.analisecidadaniaitaliana.com
set FTP_PASSWORD=W123@ftp

echo Limpando artigos antigos...
del ..\articles\*.html

echo Gerando novos artigos...
python article_generator.py

echo Publicando no servidor...
python publisher.py

echo Finalizado com sucesso!
pause