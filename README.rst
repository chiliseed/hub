=============
Chiliseed Hub
=============

Chiliseed hub is a service that manages pre-defined, production ready architectures for deploying containerized applications to AWS.
Each piece of infrastructure has a corresponding executor that manages it, and the hub combines all the pieces to provide a cohesive architecture, according to best practices.

Why?
----

1. We've deployed many projects and defined same infrastructure time and again.
2. There are many ready terraform configurations out there, open sourced for everyone to use, but it still requires knowledge of what exactly is needed and how to configure it.
3. And sometimes terraform is not enough.

This project aims to provide ready-made architecture, incorporating best practices, so that we won't need to reinvent the wheel every time.

Supported Architecture
----------------------

Network architecture
^^^^^^^^^^^^^^^^^^^^

.. image:: docs/images/networking_diagram.png


`ECS <https://aws.amazon.com/ecs/>`_ based architecture
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: docs/images/ecs_architecture.png




System Requirements
-------------------

1. Latest docker engine
2. Latest docker compose


How to Run Locally
------------------


1. Download `docker-compose.public.yml` to your machine
2. Run :code:`docker-compose up -d` from a directory containing the docker compose you downloaded
3. Install chiliseed cli: :code:`brew install chiliseed/homebrew-tools/chiliseed`


Local Development
-----------------

1. Clone the repo to your local machine, ``cd`` into the directory containing the code.
2. ``cp .env.template .env``
3. Edit the values in ``.env``
4. Download and install ``ddc-shob`` tool: https://github.com/chiliseed/django-compose-shob (readme has instructions for installation)
5. To build and start the project run: ``ddc-shob start``
6. Create a user for yourself: ```ddc-shob manage-py create_user dev@chiliseed.com 'Aa123ewq!' Demoer --is-superuser=True```


License
-------

This project is licensed under the Apache License Version 2 - see _`LICENSE.md` for more details.
