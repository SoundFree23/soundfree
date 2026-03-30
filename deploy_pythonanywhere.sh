# ==========================================
# Ruleaza asta in consola Bash pe PythonAnywhere
# Dashboard > Consoles > Bash
# ==========================================

# 1. Cloneaza repo-ul
cd ~
rm -rf soundfree
git clone https://github.com/SoundFree23/soundfree.git
cd soundfree

# 2. Instaleaza dependentele
pip install --user -r requirements.txt

# 3. Migreaza baza de date
python manage.py migrate

# 4. Colecteaza static files
python manage.py collectstatic --noinput

# 5. Adauga date demo (genuri + mood-uri)
python manage.py seed_data

# 6. Creeaza admin
python manage.py createsuperuser

echo "DONE! Acum configureaza Web App din dashboard."
