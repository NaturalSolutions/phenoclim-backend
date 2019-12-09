phenology-backend
=================

Install
-------

Create a virtualenv first::

    virtualenv phenology-backend
    source ./phenology-backend/bin/activate

Enable it and then install Python packages::

    $ pip install -r requirements.txt

.. warning:: buildout config seems to be **deprecated** and no more maintained.

Database
--------

From strach - probably useless except for testing
+++++++++++++++++++++++++++++++++++++++++++++++++
Create tables and schema::

    $ cd phenology
    $ ./manage.py syncdb
    $ ./manage.py migrate --all

Settings
--------
Copy file::

    cp phenology/phenology/settings_local.py.in phenology/phenology/settings_local.py

Then edit it to update at least DB role password.

Migration after each model changes
----------------------------------
::

    $ cd phenology
    $ ./manage.py schemamigration backend --auto

Run Server
----------
::

    $ cd phenology
    $ ./manage.py runserver 127.0.0.1:8000


Deployment of new features
--------------------------
::
    $ git status

Stash instance configuration
::
    $ git stash

Add updates
::
    $ git pull origin master

If model changes
::
    $ ./manage.py migrate backend (--delete-ghost-migrations if scripts are deleted manually)


