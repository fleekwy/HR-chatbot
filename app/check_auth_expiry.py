from datetime import datetime, timedelta
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from app.storage import user_storage
from app.handlers import UserStates


async def check_auth_expiry(bot: Bot, dispatcher: Dispatcher):
    while True:
        await asyncio.sleep(60)  # Проверка каждую минуту
        now = datetime.now()

        # Создаем копию словаря, чтобы избежать проблем с изменением во время итерации
        users_copy = user_storage.copy()

        for user_id, user_data in users_copy.items():
            if (user_data.last_auth and user_data.last_auth is not None and
                    (now - user_data.last_auth) > timedelta(minutes=1)):
                try:
                    print(f"[DEBUG] Пользователь {user_id} просрочил авторизацию")

                    # Отправка сообщения
                    await bot.send_message(user_id, "Ваша сессия истекла. Пожалуйста, введите логин снова:")

                    # Перевод в состояние UserStates.login
                    storage_key = StorageKey(bot_id=bot.id, user_id=user_id, chat_id=user_id)
                    state = FSMContext(storage=dispatcher.storage, key=storage_key)
                    await state.set_state(UserStates.login)

                    # Сброс last_auth
                    user_data.last_auth = None

                except Exception as e:
                    print(f"Ошибка при обработке пользователя {user_id}: {e}")
