# Django Site

Докеризированный сайт на Django для экспериментов с Kubernetes.

Внутри контейнера Django приложение запускается с помощью Nginx Unit, не путать с Nginx. Сервер Nginx Unit выполняет сразу две функции: как веб-сервер он раздаёт файлы статики и медиа, а в роли сервера-приложений он запускает Python и Django. Таким образом Nginx Unit заменяет собой связку из двух сервисов Nginx и Gunicorn/uWSGI. [Подробнее про Nginx Unit](https://unit.nginx.org/).

## Как подготовить окружение к локальной разработке

Код в репозитории полностью докеризирован, поэтому для запуска приложения вам понадобится Docker. Инструкции по его установке ищите на официальных сайтах:

- [Get Started with Docker](https://www.docker.com/get-started/)

Вместе со свежей версией Docker к вам на компьютер автоматически будет установлен Docker Compose. Дальнейшие инструкции будут его активно использовать.

## Как запустить сайт для локальной разработки

Запустите базу данных и сайт:

```shell
$ docker compose up
```

В новом терминале, не выключая сайт, запустите несколько команд:

```shell
$ docker compose run --rm web ./manage.py migrate  # создаём/обновляем таблицы в БД
$ docker compose run --rm web ./manage.py createsuperuser  # создаём в БД учётку суперпользователя
```

Готово. Сайт будет доступен по адресу [http://127.0.0.1:8000](http://127.0.0.1:8000). Вход в админку находится по адресу [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

## Как вести разработку

Все файлы с кодом django смонтированы внутрь докер-контейнера, чтобы Nginx Unit сразу видел изменения в коде и не требовал постоянно пересборки докер-образа -- достаточно перезапустить сервисы Docker Compose.

### Как обновить приложение из основного репозитория

Чтобы обновить приложение до последней версии подтяните код из центрального окружения и пересоберите докер-образы:

``` shell
$ git pull
$ docker compose build
```

После обновлении кода из репозитория стоит также обновить и схему БД. Вместе с коммитом могли прилететь новые миграции схемы БД, и без них код не запустится.

Чтобы не гадать заведётся код или нет — запускайте при каждом обновлении команду `migrate`. Если найдутся свежие миграции, то команда их применит:

```shell
$ docker compose run --rm web ./manage.py migrate
…
Running migrations:
  No migrations to apply.
```

### Как добавить библиотеку в зависимости

В качестве менеджера пакетов для образа с Django используется pip с файлом requirements.txt. Для установки новой библиотеки достаточно прописать её в файл requirements.txt и запустить сборку докер-образа:

```sh
$ docker compose build web
```

Аналогичным образом можно удалять библиотеки из зависимостей.

<a name="env-variables"></a>
## Переменные окружения

Образ с Django считывает настройки из переменных окружения:

`SECRET_KEY` -- обязательная секретная настройка Django. Это соль для генерации хэшей. Значение может быть любым, важно лишь, чтобы оно никому не было известно. [Документация Django](https://docs.djangoproject.com/en/3.2/ref/settings/#secret-key).

`DEBUG` -- настройка Django для включения отладочного режима. Принимает значения `TRUE` или `FALSE`. [Документация Django](https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-DEBUG).

`ALLOWED_HOSTS` -- настройка Django со списком разрешённых адресов. Если запрос прилетит на другой адрес, то сайт ответит ошибкой 400. Можно перечислить несколько адресов через запятую, например `127.0.0.1,192.168.0.1,site.test`. [Документация Django](https://docs.djangoproject.com/en/3.2/ref/settings/#allowed-hosts).

`DATABASE_URL` -- адрес для подключения к базе данных PostgreSQL. Другие СУБД сайт не поддерживает. [Формат записи](https://github.com/jacobian/dj-database-url#url-schema).

# Django Website in Minikube

## Установка и запуск

### 1. Подготовка секретов

Перед развертыванием приложения необходимо создать секреты. Создайте директорию `k8s/secrets` и добавьте в нее два файла:

#### django-secrets.yaml:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: django-secrets
type: Opaque
stringData:
  SECRET_KEY: "your-super-secret-key-here" 
  DATABASE_URL: "postgres://test_k8s:your-password@postgres-service:5432/test_k8s" 
```

#### postgres-secrets.yaml:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
type: Opaque
stringData:
  POSTGRES_DB: test_k8s
  POSTGRES_USER: test_k8s
  POSTGRES_PASSWORD: your-password 
```

### 2. Применение секретов

```bash
kubectl apply -f k8s/secrets/
```

### 3. Развертывание приложения

```bash
kubectl apply -f k8s/
```

### 4. Настройка Ingress и доступа к приложению

1. Включите Ingress в Minikube:
```bash
minikube addons enable ingress
```

2. Добавьте в файл hosts (Windows: C:\Windows\System32\drivers\etc\hosts, Linux/Mac: /etc/hosts) следующую строку:
```
127.0.0.1 star-burger.test
```

3. Запустите туннель Minikube (в отдельном терминале):
```bash
minikube tunnel
```

После этого сайт будет доступен по адресу http://star-burger.test

## Важно!

- Директория `k8s/secrets` добавлена в `.gitignore` и не должна попадать в репозиторий
- Храните файлы с секретами в безопасном месте
- Используйте разные пароли для разных окружений (development, staging, production)
- Для работы Ingress необходимо, чтобы туннель Minikube был постоянно запущен

## Очистка сессий (CronJob)

Для регулярной очистки сессий в Kubernetes настроен `CronJob`.

### Применение CronJob

```bash
kubectl apply -f django-clearsessions-cronjob.yaml
```

### Проверка статуса

Вы можете проверить статус `CronJob` с помощью следующей команды:

```bash
kubectl get cronjob django-clearsessions
```

### Ручной запуск

Для тестирования вы можете запустить `Job` из `CronJob` вручную:

```bash
kubectl create job --from=cronjob/django-clearsessions manual-clearsessions
```

После этого вы можете проверить статус запущенной `Job`:

```bash
kubectl get jobs
```
