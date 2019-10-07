echo "Creating missing migrations"
python manage.py makemigrations

echo "Migrating..."
python manage.py migrate

if [ "$?" = "1" ]; then
  echo "Failed to run migration"
  exit 1
fi

echo "Running server"
python manage.py runserver 0.0.0.0:8000
