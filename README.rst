========================
Chiliseed Control Center
========================

Control center is a service that comes with production ready, pre-defined and optimized architectures
for deploying projects to AWS. Each piece of infrastructure is configured using terraform.
Chiliseed combines all the pieces to provide a cohesive architecture, according to best practices.

Why?
----

We've deployed many projects and defined same infrastructure time and again. There are many ready terraform configurations
out there, open sourced for everyone to use, but it still requires knowledge of what exactly is needed and then how to configure it.
This project aims to provide ready-made architecture, incorporating best practices, so that we won't need to re-invent the wheel.

System Requirements
-------------------

1. Latest docker engine
2. Latest docker compose


How To Install
--------------

1. Clone the repo to your local machine, ``cd`` into the directory containing the code.
2. ``cp .env.template .env``
3. Edit the values in ``.env``
4. Download and install ``ddc-shob`` tool: https://github.com/chiliseed/django-compose-shob (readme has instructions for installation)
5. To build and start the project run: ``ddc-shob start``
6. Create a user for yourself: ```docker-compose exec api python manage.py create_user dev@chiliseed.com 'Aa123ewq!' Demoer --is-superuser=True```
