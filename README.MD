# Wallet API FastAPI

## Описание

Этот проект представляет собой API для управления кошельками с использованием **FastAPI** и **SQLAlchemy** для работы с базой данных PostgreSQL. В качестве очереди для обработки операций используется **Redis**. Проект включает в себя возможность создания кошельков, пополнения баланса и снятия средств. Все операции выполняются асинхронно, с использованием очередей для обработки запросов.

## Технологии

- **FastAPI** — фреймворк для создания веб-приложений.
- **PostgreSQL** — реляционная база данных для хранения информации о кошельках.
- **Redis** — система управления очередями для асинхронной обработки операций.
- **SQLAlchemy** — ORM для работы с базой данных.
- **PgBouncer** — пула соединений с PostgreSQL для оптимизации работы с базой данных.

## Архитектура

Проект использует несколько ключевых компонентов:

1. **FastAPI** - предоставляет API для взаимодействия с кошельками, обработки депозитов и снятия средств.
2. **Redis** - используется для управления очередями, где каждый запрос на операцию с кошельком помещается в очередь, и затем обрабатывается воркером.
3. **PostgreSQL** - хранит информацию о кошельках и их балансе.
4. **PgBouncer** - оптимизирует работу с базой данных, управляя подключениями к PostgreSQL.

## Запуск проекта

### Требования

1. Убедитесь, что у вас установлены **Docker** и **Docker Compose**.
2. Уcтановите виртуальное окружение командой:
    ```bash
   python -m venv .venv
3. Установите зависимости
    ```bash
   pip install -r requirements.txt

### Шаги для запуска через docker

1. Клонируйте репозиторий:
   ```bash
   git clone <repository_url>
   cd walletapi_fastapi
   
2. Запустите проект используя команду:
    ```bash
   docker-compose up --build

3. Для отключения используйте:
    ```bash
   docker-compose down
    ```
   
### Тестирование
1. Установите зависимости для тестирования:
    ```bash
   pip install -r tests/requirements_test.txt
    ```
2. Используйте команду: 
    ```bash
   pytest tests\
    ```
3. Или используйте такую команду, для более подробной статистики и для остановки теста после падения например 5 тестов
    ```bash
   pytest tests/ --maxfail=5 --disable-warnings -v
    ```
   
### Нагрузочное тестирование (при желании)
Перед тем как запустить тестирование, нужно создать кошелек через ручку api/v1/wallets, и вставить его в файл locust в 
переменную WALLET_UUID.
1. Запустить проект 
   ```bash
   docker-compose up --build
    ```
2. Установить locust
   ```bash
   pip install locust
    ```
   
3. Перейти в директорию locust
   ```bash
   cd locust
    ```
   
4. Запустить 
   ```bash
   locust
    ```
### Зачем использовать Redis и очереди?

В этом проекте Redis используется как очередь для обработки операций с кошельками. Это позволяет эффективно управлять запросами и снижать нагрузку на систему при обработке большого объема операций, что особенно важно для обеспечения высокой производительности (1000RPS).


Redis служит в качестве посредника между различными частями системы. Когда система получает запросы (например, на депозиты или снятие средств с кошельков), операции не выполняются немедленно, а помещаются в очередь Redis. Это позволяет обработать эти задачи асинхронно, не блокируя основной поток выполнения приложения.

 В случае сбоя или ошибки Redis позволяет просто перенаправить задачи в очередь для повторной обработки, тем самым минимизируя влияние на основные процессы.