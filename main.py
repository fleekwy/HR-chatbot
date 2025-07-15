import asyncio
from aiogram import Bot, Dispatcher
import os
from dotenv import load_dotenv
from app.handlers import router
from aiogram.fsm.storage.memory import MemoryStorage
from app.check_auth_expiry import check_auth_expiry

load_dotenv()


async def main():
    # Читаем токен из переменных окружения
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("Токен бота не найден в .env!")

    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # начинаем поллинг: бот часто обращается к Telegram и спрашивает, не пришло ли обновление
    dp.include_router(router)
    task = None

    try:
        print("Бот запущен...")
        # Запускаем проверку авторизации как фоновую задачу
        task = asyncio.create_task(check_auth_expiry(bot, dp))

        await dp.start_polling(bot)
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:

        task.cancel()  # Отменяем фоновую задачу
        try:
            await task  # Ждем завершения задачи
        except asyncio.CancelledError:
            pass
        await bot.session.close()
        print("Бот отключён")


if __name__ == '__main__':  # помогает обезопасить от ошибки, если некоторый левый main файл был импортирован
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Принудительное завершение...')
