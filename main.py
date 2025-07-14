import asyncio
from aiogram import Bot, Dispatcher

from app.handlers import router

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # начинаем поллинг: бот часто обращается к Telegram и спрашивает, не пришло ли обновление
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':  # помогает обезопасить от ошибки, если некоторый левый main файл был импортирован
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот отключился')
