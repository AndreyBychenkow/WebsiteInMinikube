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

Готово. Сайт будет доступен по адресу [http://localhost:8080](http://localhost:8080). Вход в админку находится по адресу [http://localhost:8080](http://localhost:8080/admin).

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

# Развертывание в Minikube

## 1. Подготовка кластера

Убедитесь, что у вас установлен `minikube` и `kubectl`.

Запустите Minikube:
```shell
minikube start
```

Включите addon `ingress`, который необходим для маршрутизации внешнего трафика к сервисам:
```shell
minikube addons enable ingress
```

## 2. Создание секретов

Секреты содержат чувствительные данные (пароли, ключи) и не должны храниться в репозитории. Для развертывания вам нужно создать свой собственный файл с секретами.

Скопируйте шаблон:
```shell
cp k8s/secrets.yaml.template k8s/secrets.yaml
```

Затем откройте `k8s/secrets.yaml` и замените плейсхолдеры `<your-django-secret-key>` и `<your-db-password>` на ваши реальные значения.

**ВАЖНО:** Пароль в `DATABASE_URL` и `POSTGRES_PASSWORD` должен совпадать.

Примените секреты к кластеру. **Это нужно сделать до развертывания приложения.**
```shell
kubectl apply -f k8s/secrets.yaml
```

## 2.1. Установка PostgreSQL через официальный Helm chart

PostgreSQL устанавливается с помощью официального Helm chart от Bitnami. Это рекомендуемый способ установки, так как он обеспечивает:
- Стабильность и поддержку от официальных разработчиков
- Автоматическое обновление и управление конфигурацией
- Встроенные механизмы безопасности и лучшие практики

### Шаг 1: Добавление официального репозитория Bitnami

```sh
# Добавляем официальный репозиторий Bitnami
helm repo add bitnami https://charts.bitnami.com/bitnami

# Обновляем информацию о чартах
helm repo update
```

### Шаг 2: Установка PostgreSQL

```sh
# Устанавливаем PostgreSQL с настройкой пользователя, пароля и базы данных
helm install my-postgres bitnami/postgresql \
  --set auth.username=test_k8s \
  --set auth.password=OwOtBep9Frut \
  --set auth.database=test_k8s
```

Параметры установки:
- `auth.username`: имя пользователя базы данных
- `auth.password`: пароль пользователя
- `auth.database`: название базы данных
- Имя релиза: `my-postgres` (это префикс для всех создаваемых ресурсов)

### Шаг 3: Проверка установки

```sh
# Проверяем, что под PostgreSQL запущен
kubectl get pods

# Проверяем созданный сервис
kubectl get svc

# Проверяем логи пода (замените my-postgres-postgresql-0 на актуальное имя пода)
kubectl logs my-postgres-postgresql-0
```

### Шаг 4: Получение информации для подключения

После установки PostgreSQL будет доступен внутри кластера по следующему адресу:
```
my-postgres-postgresql.default.svc.cluster.local:5432
```

Эти данные уже настроены в секретах Django (`k8s/secrets.yaml`):
- Имя хоста: `my-postgres-postgresql.default.svc.cluster.local`
- Порт: `5432`
- База данных: `test_k8s`
- Пользователь: `test_k8s`
- Пароль: совпадает с значением в `auth.password`

### Важные примечания:

1. Убедитесь, что значения `auth.username`, `auth.password` и `auth.database` совпадают с теми, что указаны в `k8s/secrets.yaml`
2. Helm chart создаст PersistentVolume для хранения данных автоматически
3. По умолчанию создается одна реплика PostgreSQL. Для production окружения рекомендуется настроить репликацию
4. Для удаления PostgreSQL используйте команду: `helm uninstall my-postgres`

## 3. Развертывание приложения

Примените все манифесты из директории `k8s/`:
```shell
kubectl apply -f k8s/
```

Запустите Job для применения миграций базы данных:
```shell
kubectl apply -f k8s/django-migrate-job.yaml
```

## 4. Настройка доступа к сайту

Чтобы получить доступ к приложению по доменному имени `star-burger.test`, необходимо связать этот домен с IP-адресом, который предоставляет Minikube.

В **отдельном терминале** запустите `minikube tunnel`. Этот процесс должен оставаться активным.
```shell
minikube tunnel
```
Туннель предоставит внешний IP-адрес для сервисов типа `LoadBalancer`, который используется нашим Ingress-контроллером.

Теперь добавьте следующую запись в ваш файл `hosts`:
- **Windows:** `C:\Windows\System32\drivers\etc\hosts`
- **Linux/macOS:** `/etc/hosts`

```
127.0.0.1 star-burger.test
```

## 5. Проверка

После выполнения всех шагов сайт должен быть доступен в браузере по адресу http://star-burger.test. Админка находится по адресу http://star-burger.test/admin/.

## Управление CronJob для очистки сессий

Для регулярной очистки старых сессий в базе данных используется `CronJob`.

Примените манифест:
```shell
kubectl apply -f django-clearsessions-cronjob.yaml
```

Проверить статус `CronJob` можно командой:
```shell
kubectl get cronjob django-clearsessions
```

Для ручного запуска задачи (например, для теста) выполните:
```shell
kubectl create job --from=cronjob/django-clearsessions manual-clearsessions-test
```

## Как задеплоить код: деплой тестового nginx через Service

1. **Создай pod с nginx**  
   Применить манифест:
   ```sh
   kubectl apply -f k8s/simple-pod.yaml -n default
   ```

2. **Создай Service для nginx**  
   Применить манифест:
   ```sh
   kubectl apply -f k8s/nginx-service.yaml -n default
   ```

3. **Проверь, что pod и service созданы:**
   ```sh
   kubectl get pods -n default
   kubectl get svc -n default
   ```

4. **Проверь доступность nginx через NodePort:**
   - Узнай порт:
     ```sh
     kubectl get svc nginx-service -n default
     ```
   - Открой в браузере:  
     `http://localhost:<nodeport>`  
     (например, если NodePort 30080 — http://localhost:30080)

## Как подготовить dev-окружение для подключения к Managed PostgreSQL через SSL

1. **Создайте Secret с SSL-сертификатом:**
   ```sh
   kubectl apply -f k8s/<your-ssl-cert-secret>.yaml -n <your-namespace>
   ```
   (или создайте вручную через Lens/GUI)

2. **Создайте Secret с параметрами подключения к БД:**
   ```sh
   kubectl apply -f k8s/<your-db-secret>.yaml -n <your-namespace>
   ```

3. **Запустите тестовый pod для проверки монтирования сертификата:**
   ```sh
   kubectl apply -f k8s/<your-test-pod-manifest>.yaml -n <your-namespace>
   ```

4. **Проверьте наличие сертификата в pod-е:**
   ```sh
   kubectl exec -it <your-test-pod-name> -n <your-namespace> -- ls -l /root/.postgresql/
   ```

5. **Подключитесь к базе через psql:**
   ```sh
   kubectl exec -it <your-test-pod-name> -n <your-namespace> -- bash
   psql "host=<db-host> port=<db-port> dbname=<db-name> user=<db-user> password=<db-password> sslmode=require"
   ```

6. **Если видите приглашение psql (`<your-namespace>,=>`) — всё работает!**
