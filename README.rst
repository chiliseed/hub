==================
Control Center API
==================

Control Center is the backend for all interactions with Chiliseed.

Local Environment Requirements
------------------------------

1. Docker engine >= 19.03.2
2. Docker compose >= 1.24.1
3. Python == 3.7


How To Install
--------------

1. Clone the repo to your local machine, ``cd`` into the directory containing the code.
2. ``cp .env.template .env``
3. Edit the values in ``.env``
4. Download and install ``ddc-shob`` tool: https://github.com/chiliseed/django-compose-shob (readme has instructions for installation)
5. To build and start the project run: ``ddc-shob start``
6. Create a user for yourself: ```docker-compose exec api python manage.py create_user dev@chiliseed.com 'Aa123ewq!' Demoer --is-superuser=True```
