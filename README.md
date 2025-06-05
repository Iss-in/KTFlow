# KTFlow
A Knowledge Sharing Platform based on Django that allows users to create sessions and upload attachments

## Setup Instructions
### deploying as docker containers
- Run `docker compose up -d` from base directory of the project to run as dockerized containers
- If you have your own setup of redis or postgres, change the relevant details in .env before running above
### running locally 
- ensure postgres is running locally, and update the default config parameters in settings.py
- run redis and start celery by `celery -A KTFlow  worker --loglevel=info --concurrency=2` from the project base directory
- start django app by ```python manage.py makemigrations  && python manage.py migrate && python manage.py runserver```


## Postman Collection
[Collection file](https://gist.github.com/Iss-in/6d5d868fb07fe7dac28cc8a9053f9c87)

## sample api usage

### register
```
POST http://localhost:8000/api/auth/register/
{
    "name": "kush",
    "email": "kush@example.com",
    "password": "kush1234"
}
```
Response: Returns refresh and access token

### login
```
POST http://localhost:8000/api/auth/login/
{
    "email": "kush@example.com",
    "password": "kush1234"
}
```
response -> refresh token and access token


### add KT
```
POST http://localhost:8000/api/kt-sessions/
{
    "title": "KT from kushagra",
    "description": "Test KT"
}
```

### add attachment
```
POST http://localhost:8000/api/attachments/create/
{
  "session_id": 1,
  "file_type": "audio",
  "file_url": "https://example.com/audio.mp3"
}
```

### get Shareable URL
```
POST http://localhost:8000/api/kt-sessions/get_sharing_url/{session_id}/
```
response -> shareable_url

### access KT via sharable URL
```aiignore
POST http://localhost:8000/api/{shareable_url}
```
response -> kt_session