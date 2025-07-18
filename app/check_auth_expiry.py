from datetime import datetime, timedelta
# Пример:
# current_time = datetime.now() - Текущая дата и время
# expiry_date = datetime.now() + timedelta(days=7) - Дата через 7 дней

import asyncio
# await asyncio.sleep(5) - Приостановка на 5 секунд

# Основные классы из aiogram 3.x:
# Bot - класс для взаимодействия с Telegram Bot API
# Dispatcher - центральный класс для обработки обновлений (update)
from aiogram import Bot, Dispatcher

# Работа с машиной состояний (FSM)
from aiogram.fsm.context import FSMContext  # Контекст для управления состоянием пользователя
from aiogram.fsm.storage.base import StorageKey  # Ключ для доступа к хранилищу состояний

# Кастомные модули
from app.storage import user_storage  # Кастомное хранилище данных пользователей - заменится на БД
from app.handlers import UserStates  # Кастомные состояния FSM


# Функция проверяет истекла ли сессия (7 дней) каждые два часа - потом удалю
async def check_auth_expiry(bot: Bot, dispatcher: Dispatcher):
    while True:
        await asyncio.sleep(7200)  # Проверка каждые два часа (спит два часа - потом проверяет)
        now = datetime.now()

        # Создаем копию словаря, чтобы избежать проблем с изменением во время итерации ??
        users_copy = user_storage.copy()

        # Перебираем копию словаря users_copy (копия нужна, чтобы избежать изменений во время итерации)
        for user_id, user_data in users_copy.items():

            # Проверяем два условия в одном выражении:
            # 1. Проверка на None явно
            # 2. Разница между текущим временем (now) и last_auth больше 7 дней
            if user_data.last_auth is not None and (now - user_data.last_auth) > timedelta(days=7):
                try:
                    # Логируем информацию о просрочке авторизации
                    print(f"[DEBUG] Пользователь {user_id} просрочил авторизацию")

                    # Отправляем пользователю сообщение о необходимости повторной авторизации
                    await bot.send_message(user_id, "Ваша сессия истекла. Пожалуйста, введите логин снова:")

                    # Создаем ключ для доступа к хранилищу состояний FSM и обращению к состоянию конкретного юзера
                    # (используем user_id как chat_id, предполагая личные чаты)
                    storage_key = StorageKey(bot_id=bot.id, user_id=user_id, chat_id=user_id)

                    # Создаем контекст состояния для конкретного пользователя
                    state = FSMContext(storage=dispatcher.storage, key=storage_key)

                    # Устанавливаем состояние пользователя в UserStates.login
                    # (переводим его на этап ввода логина)
                    await state.set_state(UserStates.login)

                    # Сбрасываем дату последней авторизации
                    user_data.last_auth = None

                except Exception as e:
                    # Ловим любые исключения при обработке пользователя
                    # (например, если бот заблокирован или пользователь не найден)
                    print(f"Ошибка при обработке пользователя {user_id}: {e}")
