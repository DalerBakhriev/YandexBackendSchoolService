## REST API service as entrance test in Yandex backend school

### Requirements: Docker.

### Run

```sh
git clone https://github.com/DalerBakhriev/YandexBackendSchoolService
cd YandexBackendSchoolService
```

Then create .env file (or rename .env.example) in project root and set environment variables for application:

```sh
touch .env
echo POSTGRES_HOST=0.0.0.0 >> .env
echo POSTGRES_USER=user >> .env
echo POSTGRES_PASSWORD=password >> .env
echo POSTGRES_DB=citizens_db >> .env
echo ADMIN_LOGIN=admin_login >> .env
echo ADMIN_PASSWORD=admin_password >> .env
```

Run application with docker-compose:

```sh
docker-compose up
```
