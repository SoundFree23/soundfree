@echo off
cd /d C:\Users\user\Desktop\python
echo.
echo ========================================
echo   Creare cont administrator
echo ========================================
echo.
venv\Scripts\python manage.py createsuperuser
pause
