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

1. Create virtual environment for the project:

    .. code-block:: bash

        mkdir chiliseed
        cd chiliseed
        mkdir backend
        cd backend
        python3 -m venv .venv

2. Clone the repo inside ``backend``
3. Install local requirements:

    .. code-block:: bash

        pip install -e cli_tools

    This will install `tools` package, that contains cli utilities for easy
    interactions with the environment.


4. Run local environment:
    .. code-block:: bash

        tools start


Local tools
-----------

``tools.py`` is a collection of cli shortcut for common action while developing.

To see all available commands run:

    .. code-block:: bash

        ./tools.py --help
