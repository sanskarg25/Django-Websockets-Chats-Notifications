# Vendor Management



## Getting started

Vendor Management is a web application built using Django framework to streamline and manage vendors effectively. It has some features including Vendors CRUD, Purchase order CRUD and Historical Performance metrics for vendors.


## Setup [Windows]

git clone https://gitlab.com/sanskargandhi2000/vendor-management.git
cd vendor-management

Then, create a virtual environment before starting the applciation server, use the command - 
"python -m venv env" or "virtualenv env"


env\Scripts\activate  // to activate the virtual env

Make sure you virtualenv is activated throughout.

You need to create a postgres database.
Also, create a .env file in main directory as of requirements.txt and include your related details - 


DB_USERNAME = "postgres"
DB_PASSWORD = "your_password"
DB_NAME = "vendor_management"
DB_HOST = "localhost"
DB_PORT = "5432"
 
SERVER_HOST = "http://localhost:8000/"
UI_HOST = "http://localhost:8000/"


## Installation

pip install -r requirements.txt

This command will install all the required libraries and packages for starting up the server.

Now,
python manage.py makemigrations


python manage.py migrate

Use the above commands to have models in place with mentioned database.

## Starting the server

python manage.py createsuperuser  // to have the access to django admin panel

python manage.py runserver // localhost


python manage.py runserver "ip:port" // for having it externally available


## Postman Documentation

Please find out the documentation related to created APIs for reference.

url - https://documenter.getpostman.com/view/31783514/2sA3JGf4Kq
