# Асинхронная библиотека стандартной библиотеки Python
# Используется для работы с асинхронным кодом (корутины, задачи, event loop)
# КОРУТИНЫ — это специальные функции, которые могут приостанавливать своё выполнение и возобновлять
# его позже, не теряя контекст. Они используются для асинхронного программирования и позволяют эффективно
# работать с I/O-операциями (сетевые запросы, чтение файлов и т.д.), не блокируя основной поток.
import asyncio

# Библиотека с методами для логирования различного типа
import logging

# Основные классы из aiogram 3.x:
# Bot - класс для взаимодействия с Telegram Bot API
# Dispatcher - центральный класс для обработки обновлений (update)
from aiogram import Bot, Dispatcher, BaseMiddleware

from app.issue_statistics import Database
from app.sqlite_storage import SQLiteStorage

# Модуль стандартной библиотеки Python для работы с операционной системой
# Используется для доступа к переменным окружения, путям файлов и т.д.
import os

# Библиотека для загрузки переменных окружения из .env файла
# Позволяет хранить чувствительные данные (токены бота) отдельно от кода
from dotenv import load_dotenv

# Импорт роутера из вашего приложения
# Содержит обработчики сообщений и команд для бота
from app.handlers import router
from config import FSM_DB_PATH

load_dotenv()  # Функция load_dotenv() из библиотеки python-dotenv загружает переменные окружения
# из файла .env в текущее окружение Python

# Настройка базовой конфигурации логирования для всего приложения:
# - level=logging.INFO - устанавливает уровень логирования (INFO и выше)
# - По умолчанию выводит сообщения в консоль с форматом: "LEVEL:logger_name:message"
# - Другие доступные уровни: DEBUG, WARNING, ERROR, CRITICAL
logging.basicConfig(level=logging.INFO)

# Создание объекта логгера для текущего модуля:
# - __name__ автоматически подставляет имя текущего модуля (например "app.auth_manager")
# - Позволяет идентифицировать источник лог-сообщений
# - Лучше использовать чем logging напрямую, так как:
#   1. Позволяет индивидуально настраивать логгеры для разных модулей
#   2. Поддерживает иерархию логгеров через точку в имени (например "app" и "app.auth")
logger = logging.getLogger(__name__)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")


class AuthBotMiddleware(BaseMiddleware):
    def __init__(self, auth_bot: Database):
        self.auth_bot = auth_bot

    async def __call__(self, handler, event, data):
        data["auth_bot"] = self.auth_bot
        return await handler(event, data)


# главная функция
async def main():

    # Читаем токен из переменных окружения
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("Токен бота не найден в .env!")  # если токен не был найден

    # В этом коде инициализируются основные компоненты для работы бота на aiogram 3.x.
    bot = Bot(token=bot_token)  # Создаётся экземпляр класса Bot, который отвечает за взаимодействие с Telegram Bot API
    # storage = MemoryStorage()  # Создаётся хранилище состояний (FSM — Finite State Machine) в оперативной памяти

    storage = SQLiteStorage(db_path=FSM_DB_PATH)  # Хранилище в оперативной памяти - явно передаем путь
    dp = Dispatcher(storage=storage)  # Создаётся диспетчер (Dispatcher) — центральный компонент aiogram, который:
    # принимает обновления от Telegram (сообщения, команды, колбэки), перенаправляет их в ваши обработчики (роутеры).
    # Telegram --> Bot --> Dispatcher --> Router --> Handlers

    auth_bot = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

    await auth_bot.connect()
    print(auth_bot.pool)

    dp.update.middleware(AuthBotMiddleware(auth_bot))
    dp.include_router(router)  # Подключает роутер (группу обработчиков) к диспетчеру бота

    # Запуск бота
    try:
        logger.info("Бот запущен...")

        # начинаем поллинг: бот часто обращается к Telegram и спрашивает, не пришло ли обновление
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка: {e}")

    # Завершение работы бота
    finally:
        await bot.session.close()  # освобождает ресурсы (HTTP-соединения)
        await auth_bot.close()  # закрываем сессию бота
        logger.info("Бот отключён")


if __name__ == '__main__':  # помогает обезопасить от ошибки, если некоторый левый main-файл был импортирован
    try:
        asyncio.run(main())  # запускаем асинхронную функцию main
    except KeyboardInterrupt:
        logger.warning('Принудительное завершение...')

# Структура бота:
#
# HR-chatbot/
# ├── .venv/                        # Виртуальное окружение (пока не создано)
# ├── app/                          # Основная папка приложения
# │   ├── handlers.py               # Обработчики сообщений
# │   ├── keyboards.py              # Клавиатуры и кнопки
# │   ├── sqlite_storage.py         # Работа с SQLite
# │   ├── issue_statistics.py       # Статистика вопросов
# │   ├── backup_postgre.sql        #
# │   ├── email_key.py              #
# │   ├── valueai_client.py         # Клиент для ValueAI
# │   └── auto_valueai.py           # Интеграция с AI (если часть ядра)
# ├── config.py                     # Глобальные настройки
# ├── email_key.py                  # Ключи и email
# ├── main.py                       # Запуск бота
# ├── requirements.txt              # Зависимости
# ├── states.db                     # База данных состояний
# ├── Dockerfile                    #
# ├── docker-compose.yml            #
# ├── .gitignore                    # Игнорируемые файлы
# └── .env                          # Переменные окружения (пароли)
