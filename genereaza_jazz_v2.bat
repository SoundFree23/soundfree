@echo off
cd /d C:\Users\user\Desktop\python
echo.
echo ================================================
echo   SoundFree.ro - Jazz Lounge v2.0 (HD)
echo ================================================
echo.
echo Instalez numpy si scipy...
venv\Scripts\pip install numpy scipy -q
echo.
echo Generez melodia... (1-3 minute)
echo.
venv\Scripts\python generate_jazz_v2.py
echo.
pause
