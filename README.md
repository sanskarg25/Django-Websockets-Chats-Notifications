# Websockets Chats Notifications



## Getting started

This is a tutorial for creating a chat application with notifications integrated using Django-Websockets as tech stack.

## Setup [Windows]

go to the directory where you want to clone

cmd - git clone https://github.com/sanskarg25/Django-Websockets-Chats-Notifications.git

cd "created dir"

Then, create a virtual environment before starting the applciation server, use the command - 

"python -m venv env" or "virtualenv env"


env\Scripts\activate  // to activate the virtual env

Make sure you virtualenv is activated throughout.

You need to create a postgres database.
Also, create a .env file in main directory as of requirements.txt and include your related details - 


DB_USERNAME = "postgres"

DB_PASSWORD = "your_password"

DB_NAME = "your_db_name"

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

## Creating docker image

You can use two ways for setting up docker-image

### Windows User - 
Download docker desktop and there you can create image as you require or else you the below command after installing docker desktop.

CMD prompt [ run Docker desktop] -

> docker ps

> docker ps -al

> docker pull redis

> docker run -d --name "project_name"-redis -p 6379:6379 redis

> docker ps

> docker restart "project_name"-redis

### Linux User - 
refer this - https://docs.docker.com/engine/install/ubuntu/

## Starting the server

python manage.py createsuperuser  // to have the access to django admin panel

python manage.py runserver // localhost

python manage.py runserver "ip:port" // for having it externally available

## IMP Note
Working with sockets using docker, redis and daphne is bit tricky so checkout the each and every logic built to understand the functionality.
