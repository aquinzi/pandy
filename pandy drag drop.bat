:: Pandy.py wrapper for drag & drop.
:: Just drag file/folder to script & command will prompt

@echo off

(SET file=%1)

echo.
Echo   From formats: 
Echo      md (=markdown), html
echo.
ECHO   From which format?:
SET /P from=:

echo.
Echo   To formats: 
Echo      md (=markdown), html, doc (=docx), epub, odt , slides (or slide) mediawiki (or mw)
echo.
ECHO   To which format/s? (separate with spaces):
SET /P to=:

echo.
Echo   Other options: 
echo      -nohigh           no highlight
echo      -toc              include TOC
echo      -self             self contained file
echo      -hide             e-mail obfuscation (default none, set = references)
echo      -css              External CSS
echo.
ECHO   Other option/s? (separate with spaces):
SET /P options=:

python pandy.py %from% %to% %file% %options%

echo.
::@pause