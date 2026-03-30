@echo off
cd /d C:\Users\user\Desktop\python
echo.
echo ========================================
echo   SoundFree.ro — Pornire server
echo ========================================
echo.

echo [1/4] Instalez dependente...
venv\Scripts\pip install Pillow -q
echo OK

echo [2/4] Creez baza de date...
venv\Scripts\python manage.py makemigrations --noinput
venv\Scripts\python manage.py migrate --noinput
echo OK

echo [3/4] Adaug date demo...
venv\Scripts\python manage.py seed_data
echo OK

echo [4/4] Pornesc serverul...
echo.
echo ========================================
echo   Site-ul este la: http://127.0.0.1:8000
echo   Admin:  http://127.0.0.1:8000/admin
echo   Apasa CTRL+C pentru a opri
echo ========================================
echo.
venv\Scripts\python manage.py runserver

pause
