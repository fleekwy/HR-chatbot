import asyncio
from aiogram import Bot, Dispatcher
import os
from dotenv import load_dotenv
from app.handlers import router

load_dotenv()

async def main():
    # Читаем токен из переменных окружения
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("Токен бота не найден в .env!")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # начинаем поллинг: бот часто обращается к Telegram и спрашивает, не пришло ли обновление
    dp.include_router(router)

    try:
        print("Бот запущен...")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await bot.session.close()  # Закрываем сессию бота
        print("Бот отключён")


if __name__ == '__main__':  # помогает обезопасить от ошибки, если некоторый левый main файл был импортирован
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Принудительное завершение...')