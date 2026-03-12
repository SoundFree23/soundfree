import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User

USERNAME = 'admin'
EMAIL    = 'admin@soundfree.ro'
PASSWORD = 'SoundFree2025!'

if User.objects.filter(username=USERNAME).exists():
    print(f'⚠️  Userul "{USERNAME}" există deja.')
    u = User.objects.get(username=USERNAME)
    u.set_password(PASSWORD)
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print(f'✅ Parola a fost resetată la: {PASSWORD}')
else:
    User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
    print('✅ Superadmin creat cu succes!')
    print(f'   Username : {USERNAME}')
    print(f'   Parolă   : {PASSWORD}')
    print(f'   Email    : {EMAIL}')

print()
print('🔐 Intră la: http://127.0.0.1:8000/backend/login/')
print('⚠️  Schimbă parola după primul login!')
