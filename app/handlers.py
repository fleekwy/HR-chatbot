# Основные компоненты aiogram:
# F (фильтры) - для создания гибких условий в обработчиках (например, F.text == "Start"
# Router - основной инструмент для организации обработчиков сообщений (альтернатива Dispatcher в aiogram 3.x)
from aiogram import F, Router
# Message - класс для работы с текстовыми/медиа-сообщениями
# CallbackQuery - обработка нажатий на инлайн-кнопки
from aiogram.types import Message, CallbackQuery
# CommandStart - фильтр для команды /start                          ###
# Command - фильтр для любых команд (например, Command("help"))     ###
from aiogram.filters import CommandStart, Command
# CommandStart - фильтр для команды /start                          ###
# Command - фильтр для любых команд (например, Command("help"))     ###
from aiogram.fsm.state import State, StatesGroup
# FSMContext - управление состоянием пользователя (установка/получение данных)
from aiogram.fsm.context import FSMContext

# Работа с датой/временем
# datetime - для работы с датами и временем (например, фиксация времени авторизации)
# from datetime import datetime
import time

# Для логирования ошибок
import logger

# Настройки окружения
import os  # доступ к переменным окружения (os.getenv("TOKEN"))
from dotenv import load_dotenv  # загрузка переменных из .env-файла (для безопасного хранения токенов)

# Кастомные модули
import app.keyboards as kb  # Локальный модуль с клавиатурами
# from app.storage import SQLiteStorage
# from app.storage import user_storage, UserData  # user_storage - ваше хранилище данных пользователей
# UserData - класс для хранения данных пользователя
from app.valueai_client import ValueAIClient  # Кастомный клиент для работы с внешним API
from app.auth_valueai import AuthValuai  # Модуль для управления аутентификацией (получение/обновление auth-token)
from app.auth_bot import AuthBot
# from config import FSM_DB_PATH

from app.ww_the_database import connect_db, user_exists, is_authenticated, save_session, save_question_stat

# Глобальный пул
pool = None

router = Router()  # Создаем экземпляр роутера
load_dotenv('.env')  # Загружаем переменные окружения из файла .env

# Получаем логин и пароль из переменных окружения
VALUEAI_LOGIN = os.getenv("VALUEAI_LOGIN")  # Логин для аутентификации в ValueAI
VALUEAI_PASSWORD = os.getenv("VALUEAI_PASSWORD")  # Пароль для аутентификации в ValueAI

# Создаем менеджер аутентификации, передавая ему полученные учетные данные
auth_manager = AuthValuai(VALUEAI_LOGIN, VALUEAI_PASSWORD)
auth_system = AuthBot()

# Инициализируем клиент для работы с API ValueAI, передавая ему менеджер аутентификации
valueai_client = ValueAIClient(auth_manager)


# Устанавливаем кастомные состояния
class UserStates(StatesGroup):
    login = State()           # Ввод логина
    password = State()        # Ввод пароля
    auth_confirmed = State()  # Успешная авторизация
    banned = State()          # Блокировка пользователя


# Обработчик команды /start
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    global pool
    pool = await connect_db()
    await message.answer(
        "Добро пожаловать в HR-чатбот!\n\n"
        "Пожалуйста, введите ваш логин в формате name@waveaccess.global"
    )
    await state.set_state(UserStates.login)  # Сразу устанавливаем состояние UserStates.login и запускаем авторизацию


# Обработчик состояния UserStates.login
# Срабатывает, когда пользователь находится в состоянии "ввода логина"
@router.message(UserStates.login)
async def process_login(message: Message, state: FSMContext):
    # Ниже вставим поиск данного логина (если корректно ввели) в БД доступа
    # Проверяем, что логин заканчивается на "@waveaccess.global" и вообще существует ли
    if not message.text.endswith("@waveaccess.global") or not auth_system.user_exists(message.text):
        # Если проверка не пройдена - отправляем сообщение об ошибке
        await message.answer("Некорректный логин! Должен быть в формате name@waveaccess.global")
        return  # Выходим из функции, не меняя состояние -> снова запускается обработчик данного состояния

    await state.update_data(login=login)
    # ХЗ
    # # Сохраняем введенный логин в хранилище FSM 
    # # Это позволит использовать его на следующем шаге (ввод пароля)
    # data = await state.update_data(login=message.text)
    # print("Данные сохранены:", data)
    # stored = await state.get_data()
    # print("get_data сразу после обновления:", stored)
    # # state_data = await storage.debug_state(StorageKey(chat_id=message.chat.id, user_id=message.from_user.id))
    # # print(f"Состояние в БД: {state_data}")
    # print(f"Ключ состояния: chat_id={message.chat.id}, user_id={message.from_user.id}, bot_id = {message.bot.id}")

    # Меняем состояние пользователя на UserStates.password
    # Теперь бот будет ожидать ввод пароля
    await state.set_state(UserStates.password)
    # # print("До get_data в password после смены состояния:", await state.get_data()) ### как я понял, это индикатор

    # Отправляем пользователю сообщение с инструкцией
    await message.answer("Теперь введите ваш пароль:")


# Обработчик состояния ввода пароля (UserStates.password)
# Срабатывает только когда пользователь в состоянии "ввода пароля"
@router.message(UserStates.password)
async def process_password(message: Message, state: FSMContext):
    user_data = await state.get_data()
    login = user_data.get("login")
    password = message.text.strip()

    # Проверка на SQLite3
    # print(f"Ключ состояния: chat_id={message.chat.id}, user_id={message.from_user.id}, bot_id = {message.bot.id}")
    # print(f"Данные получены: {user_data}")  # ← Отладка
    # user_login = user_data.get('login')
    # user_password = message.text

    # # ФУНКЦИЯ ПРОВЕРКИ ЛОГИНА И ПАРОЛЯ В БД ДОСТУПА
    # is_confirmed = auth_system.is_authenticate(user_login, user_password)

    # if not is_confirmed:
    if not await is_authenticated(pool, login, password):
        await message.answer("Неверный пароль! Попробуйте еще раз.")  # Отправка сообщения об ошибке если пароль пустой
        return  # Выход из функции без изменения состояния

    # ЗАКОММЕНТИРОВАННОЕ НИЖЕ ОСТАЛОСЬ ОТ ПРЕЖНЕЙ РЕАЛИЗАЦИИ СОХРАНЕНИЯ ДАТЫ АВТОРИЗАЦИИ
    # # Создание нового объекта данных пользователя
    # user_data = UserData()
    #
    # # Фиксация времени последней успешной авторизации
    # user_data.last_auth = datetime.now()  # Текущее время
    #
    # # Сохранение данных пользователя в хранилище
    # # Ключ - ID пользователя Telegram (message.from_user.id)
    # user_storage[message.from_user.id] = user_data  # сохраняем

    await save_session(pool, tg_id=message.from_user.id, login=login)
    # Меняем состояние - авторизация подтверждена
    await state.set_state(UserStates.auth_confirmed)

    # Отправка сообщения об успешной авторизации
    await message.answer("Вы успешно авторизованы! Можете задавать вопросы!")


# Обработчик состояния UserStates.auth_confirmed
@router.message(UserStates.auth_confirmed)
async def handle_user_message(message: Message):
    """
    Обработчик всех текстовых сообщений, не попавших в другие обработчики.
    Отправляет запрос к ИИ-модели и возвращает ответ пользователю.
    """

    # 1. Отправляем сообщение "Обработка запроса..."
    thinking_msg = await message.answer("Обработка запроса...")
    start_time = time.time()  # Засекаем время начала обработки

    try:
        # 2-. Сохраняем в статистику
        await save_question_stat(pool, message.text.strip())

        # 2. Отправляем запрос к ИИ-ассистенту
        response = await valueai_client.send_message_to_llm(message.text)

        # 3. Очищаем ответ от технической информации (все после ******)
        response = response.split('**********', 1)[0].strip()

        # 4. Проверяем, что ответ не пустой
        if not response:
            raise ValueError("Пустой ответ от ИИ")

    except Exception as e:
        # 5. Логируем ошибку для дальнейшего анализа
        logger.error(f"Ошибка обработки сообщения: {e}", message)

        # 6. Формируем запасной вариант ответа
        response = (
            "Извините, не удалось обработать ваш запрос. "
            "Попробуйте переформулировать вопрос или обратитесь позже."
        )

    # 7. Удаляем сообщение "Обработка запроса..."
    await thinking_msg.delete()

    # 8. Рассчитываем время выполнения
    processing_time = round(time.time() - start_time, 2)

    # 9. Формируем финальное сообщение с временем обработки
    final_response = (
        f"{response}\n\n"
        f"⏱ Время обработки: {processing_time} сек."
    )

    # 10. Отправляем ответ пользователю
    await message.answer(text=final_response)


# Обработчик команды /menu
@router.message(Command("menu"))
async def cmd_help(message: Message):
    # Отправляем сообщение с инлайн-клавиатурой main из модуля keyboards (kb)
    await message.answer(
        "Выберите необходимую кнопку:",  # Текст сообщения
        reply_markup=kb.main  # Прикрепляем клавиатуру из предварительно созданных
    )


# Обработчик нажатия на кнопку с callback_data "about_us"
@router.callback_query(F.data == "about_us")
async def about_us(callback: CallbackQuery):
    # 1. Редактируем исходное сообщение с клавиатурой:
    await callback.message.edit_text(
        "Выберите раздел:",  # Новый текст сообщения
        reply_markup=kb.about_us  # Подставляем новую клавиатуру "About us"
    )
    # 2. Подтверждаем обработку callback (обязательно!)
    await callback.answer()


# Обработчик нажатия на кнопку с callback_data "about_bot"
@router.callback_query(F.data == "about_bot")
async def about_bot(callback: CallbackQuery):
    # Отправляем всплывающее уведомление через callback.answer()
    await callback.answer(
        # Текст уведомления (макс. 200 символов)
        "Это HR-чатбот компании WaveAccess.\n"
        "Я могу ответить на ваши вопросы о работе в компании.",

        # Параметр show_alert=True делает всплывающее окно вместо временной подсказки
        show_alert=True
    )


# Обработчик для кнопки "Back" (callback_data="back_to_main")
@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    # 1. Редактируем текущее сообщение:
    await callback.message.edit_text(
        "Вы вернулись в главное меню.",  # Обновленный текст
        reply_markup=kb.main  # Возвращаем основную клавиатуру
    )
    # 2. Обязательно подтверждаем обработку callback
    await callback.answer()  # Убираем "часики" с кнопки


# Обработчик кнопки повторной авторизации
@router.callback_query(F.data == "reauthorisation")
async def reauthorisation(callback: CallbackQuery, state: FSMContext):
    # 1. Устанавливаем состояние "login" для начала процесса авторизации
    await state.set_state(UserStates.login)

    # 2. Обязательно подтверждаем обработку callback (убираем анимацию загрузки)
    await callback.answer("Начата повторная авторизация")

    # 3. Отправляем новое сообщение с инструкциями
    await callback.message.answer(
        "Пожалуйста, введите ваш логин в формате name@waveaccess.global"
    )


# Обработчик кнопки "Help" (callback_data="help")
@router.callback_query(F.data == "help")
async def about_bot(callback: CallbackQuery):
    # Отправляем всплывающее уведомление с информацией
    await callback.answer(
        "Повторная авторизация нужна на случай, если ваши данные устарели",
        show_alert=True  # Создает модальное окно, требующее подтверждения
    )
