@echo off
echo ========================================
echo   Push SoundFree pe GitHub
echo ========================================
echo.

cd /d C:\Users\user\Desktop\python

REM Sterge subfolder-ul soundfree vechi (era un clone gol)
if exist soundfree\.git (
    echo Sterg clona veche soundfree...
    rmdir /s /q soundfree
)

REM Initializeaza git daca nu exista
if not exist .git (
    echo Initializez git...
    git init
    git branch -M main
)

REM Verifica daca remote exista deja
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo Adaug remote origin...
    git remote add origin https://github.com/SoundFree23/soundfree.git
) else (
    echo Remote origin exista deja, il actualizez...
    git remote set-url origin https://github.com/SoundFree23/soundfree.git
)

echo.
echo Adaug fisierele...
git add manage.py myproject/ music/ templates/ static/ requirements.txt Procfile .gitignore create_superadmin.py

echo.
echo Creez commit...
git commit -m "SoundFree - deploy PythonAnywhere"

echo.
echo Push pe GitHub...
git push -u origin main --force

echo.
echo ========================================
echo   DONE! Codul e pe GitHub.
echo   Acum mergi pe PythonAnywhere.
echo ========================================
pause
