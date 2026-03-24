@echo off

echo Configurando credenciais FTP...
set FTP_HOST=srv1849-files.hstgr.io
set FTP_USER=u935013836.analisecidadaniaitaliana.com
set FTP_PASSWORD=W123@ftp

echo Gerando 5 novas keywords SEO...
python daily_keywords.py

echo Limpando artigos antigos...
del ..\articles\*.html

echo Gerando novos artigos...
python article_generator.py

echo Publicando no servidor...
python publisher.py

echo Finalizado com sucesso!
pause