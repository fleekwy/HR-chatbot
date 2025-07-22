# Асинхронная библиотека стандартной библиотеки Python
# Используется для работы с асинхронным кодом (корутины, задачи, event loop)

# КОРУТИНЫ — это специальные функции, которые могут приостанавливать своё выполнение и возобновлять
# его позже, не теряя контекст. Они используются для асинхронного программирования и позволяют эффективно
# работать с I/O-операциями (сетевые запросы, чтение файлов и т.д.), не блокируя основной поток.
import asyncio

# Основные классы из aiogram 3.x:
# Bot - класс для взаимодействия с Telegram Bot API
# Dispatcher - центральный класс для обработки обновлений (update)
from aiogram import Bot, Dispatcher
from app.sqlite_storage import SQLiteStorage
from pathlib import Path

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

# Реализация хранилища состояний FSM (Finite State Machine)
# MemoryStorage хранит данные в оперативной памяти (исчезают после перезапуска бота)
# from aiogram.fsm.storage.memory import MemoryStorage

# Кастомная функция для проверки истечения срока аутентификации
# Содержит логику проверки времени сессии пользователя
# from app.check_auth_expiry import check_auth_expiry

# from app.middlewares.state_recovery import StateRecoveryMiddleware

load_dotenv()  # Функция load_dotenv() из библиотеки python-dotenv загружает переменные окружения
# из файла .env в текущее окружение Python


# главная функция
async def main():
    # Читаем токен из переменных окружения
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("Токен бота не найден в .env!")  # если токен не был найден

    # В этом коде инициализируются основные компоненты для работы бота на aiogram 3.x.
    bot = Bot(token=bot_token)  # Создаётся экземпляр класса Bot, который отвечает за взаимодействие с Telegram Bot API
    # storage = MemoryStorage()  # Создаётся хранилище состояний (FSM — Finite State Machine) в оперативной памяти

    # Путь от корня проекта до states.db
    # db_path = Path(__file__).parent / "states.db"  # main.py и states.db в одной папке

    db_path = Path(__file__).parent / "states.db"
    print(f"Путь к states.db: {db_path}")
    print(f"Файл существует: {db_path.exists()}")
    storage = SQLiteStorage(db_path=FSM_DB_PATH)  # Хранилище в оперативной памяти - явно передаем путь
    dp = Dispatcher(storage=storage)  # Создаётся диспетчер (Dispatcher) — центральный компонент aiogram, который:
    # принимает обновления от Telegram (сообщения, команды, колбэки), перенаправляет их в ваши обработчики (роутеры).
    # Telegram --> Bot --> Dispatcher --> Router --> Handlers
    # ????dp.update.outer_middleware(StateRecoveryMiddleware())  # Подключение миддлваря

    dp.include_router(router)  # Подключает роутер (группу обработчиков) к диспетчеру бота

    # task = None  # заглушка

    # Запуск бота
    try:
        print("Бот запущен...")
        # task = asyncio.create_task(check_auth_expiry(bot, dp))  # Запускаем проверку авторизации как фоновую задачу

        # начинаем поллинг: бот часто обращается к Telegram и спрашивает, не пришло ли обновление
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Ошибка: {e}")

    # Завершение работы бота
    finally:
        # task.cancel()  # Отменяем фоновую задачу
        # try:
        #     await task  # Ждем завершения задачи
        # except asyncio.CancelledError:
        #     pass
        await bot.session.close()  # освобождает ресурсы (HTTP-соединения)
        print("Бот отключён")


if __name__ == '__main__':  # помогает обезопасить от ошибки, если некоторый левый main-файл был импортирован
    try:
        asyncio.run(main())  # запускаем асинхронную функцию main
    except KeyboardInterrupt:
        print('Принудительное завершение...')
