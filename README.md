coach
=====

Dashboard for the COACH project

Installation
============
    
    git clone git@github.com:ictofnwi/coach.git
    cd coach
    virtualenv venv
    . venv/bin/activate
    pip install -r requirements.txt

Setting up the database
=======================
Create settings file: (Make sure you are in the working directory)

`cp coach/settings.py.examle coach/settings.py`

Edit coach/settings.py to fill the LRS login data, then create the database:

`python manage.py syncdb`

Running
=======
(Make sure you are in the working directory)

    . venv/bin/activate
    python manage.py runserver (will by default launch at http://127.0.0.1:8000)
