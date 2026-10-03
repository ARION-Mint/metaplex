@echo off
setlocal enabledelayedexpansion
rem ================================================================
rem  make-web-videos.bat  -  Multimedia Studio
rem
rem  1. Lege deine ORIGINAL-Videos in den Ordner "videos-original"
rem     (neben dieser Datei, im Website-Hauptordner).
rem     Dateinamen am besten klein und mit Bindestrich, z.B. lumen-serum.mov
rem  2. Doppelklick auf diese Datei.
rem
rem  Fuer jedes Video, das noch keine Web-Version hat, entsteht:
rem    assets\videos\web\NAME.mp4   (max. 1280 px, 30 fps, ohne Ton)
rem    assets\posters\w-NAME.jpg    (Standbild fuer Karten und Wand)
rem  Danach wird assets\work-list.js neu geschrieben (Bilderwand).
rem  Deine Originale werden NICHT veraendert.
rem ================================================================
cd /d "%~dp0"

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo.
  echo  FFmpeg wurde nicht gefunden.
  echo  Installiere es mit:  winget install ffmpeg
  echo  und starte diese Datei danach erneut.
  echo.
  pause
  exit /b 1
)

if not exist "videos-original" mkdir "videos-original"
if not exist "assets\videos\web" mkdir "assets\videos\web"
if not exist "assets\posters" mkdir "assets\posters"

set /a made=0
for %%F in ("videos-original\*.mp4" "videos-original\*.mov" "videos-original\*.mkv" "videos-original\*.webm" "videos-original\*.avi" "videos-original\*.m4v") do (
  set "name=%%~nF"
  set "name=!name: =-!"
  if not exist "assets\videos\web\!name!.mp4" (
    echo  Web-Version: %%~nxF  ^>  !name!.mp4
    ffmpeg -hide_banner -loglevel error -y -i "%%F" -an -vf "scale='if(gt(iw,ih),min(1280,iw),-2)':'if(gt(iw,ih),-2,min(1280,ih))',fps=30,format=yuv420p" -c:v libx264 -preset slow -crf 23 -movflags +faststart "assets\videos\web\!name!.mp4"
    set /a made+=1
  )
  if not exist "assets\posters\w-!name!.jpg" (
    echo  Standbild:   w-!name!.jpg
    ffmpeg -hide_banner -loglevel error -y -ss 0.5 -i "assets\videos\web\!name!.mp4" -frames:v 1 -vf "scale='if(gt(iw,ih),720,-2)':'if(gt(iw,ih),-2,720)'" -q:v 3 "assets\posters\w-!name!.jpg"
  )
)

rem ---- Bilderwand: Liste aller Standbilder neu schreiben ----
> "assets\work-list.js" echo /* automatisch erstellt von make-web-videos.bat - nicht von Hand bearbeiten */
>> "assets\work-list.js" echo window.WORK_SHOTS=[
for %%P in ("assets\posters\w-*.jpg") do >> "assets\work-list.js" echo   "%%~nP",
>> "assets\work-list.js" echo ];

echo.
echo  Fertig. Neue Web-Videos: !made!
echo  Liste der Videos:  assets\videos\web
echo.
pause
