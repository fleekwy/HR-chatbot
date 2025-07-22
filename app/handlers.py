# Основные компоненты aiogram:
# F (фильтры) - для создания гибких условий в обработчиках (например, F.text == "Start"
# Router - основной инструмент для организации обработчиков сообщений (альтернатива Dispatcher в aiogram 3.x)
from aiogram import F, Router
from aiogram.fsm.storage.base import StorageKey
# Message - класс для работы с текстовыми/медиа-сообщениями
# CallbackQuery - обработка нажатий на инлайн-кнопки
from aiogram.types import Message, CallbackQuery
# CommandStart - фильтр для команды /start
# Command - фильтр для любых команд (например, Command("help"))
from aiogram.filters import CommandStart, Command
# CommandStart - фильтр для команды /start
# Command - фильтр для любых команд (например, Command("help"))
from aiogram.fsm.state import State, StatesGroup
# FSMContext - управление состоянием пользователя (установка/получение данных)
from aiogram.fsm.context import FSMContext

# Работа с датой/временем
# datetime - для работы с датами и временем (например, фиксация времени авторизации)
# from datetime import datetime
import time
import secrets
import string

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
from config import FSM_DB_PATH
from app.sqlite_storage import SQLiteStorage
from app.email_key import send_key_to_email

router = Router()  # Создаем экземпляр роутера
load_dotenv('.env')  # Загружаем переменные окружения из файла .env

# Получаем логин и пароль из переменных окружения
VALUEAI_LOGIN = os.getenv("VALUEAI_LOGIN")  # Логин для аутентификации в ValueAI
VALUEAI_PASSWORD = os.getenv("VALUEAI_PASSWORD")  # Пароль для аутентификации в ValueAI

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))

# Создаем менеджер аутентификации, передавая ему полученные учетные данные
auth_manager = AuthValuai(VALUEAI_LOGIN, VALUEAI_PASSWORD)
auth_bot = AuthBot()

# Инициализируем клиент для работы с API ValueAI, передавая ему менеджер аутентификации
valueai_client = ValueAIClient(auth_manager)


# Фильтр, проверяющий, что пользователь — админ
# router.message.filter(F.from_user.id.in_(ADMIN_IDS))
# router.callback_query.filter(F.from_user.id.in_(ADMIN_IDS))


# Устанавливаем кастомные состояния
class UserStates(StatesGroup):
    login = State()  # Ввод логина
    password = State()  # Ввод пароля
    auth_confirmed = State()  # Успешная авторизация
    banned = State()  # Пользователь больше не авторизован


# Состояния для админа (добавление/удаление пользователя)
class AdminStates(StatesGroup):
    login = State()
    password = State()
    admin = State()
    waiting_for_new_user = State()
    waiting_for_user_to_remove = State()


# Обработчик команды /start
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        "Добро пожаловать в HR-чатбот! Перед началом работы необходимо пройти авторизацию.\n\n"
        "Пожалуйста, введите ваш логин в формате name@waveaccess.global"
    )
    print(f'id = {message.from_user.id}')
    await state.set_state(UserStates.login)  # Сразу устанавливаем состояние UserStates.login и запускаем авторизацию


# 1. Стартовые команды (без состояний)
# Обработчик команды /menu
@router.message(Command("menu"))
async def cmd_help(message: Message):
    # Отправляем сообщение с инлайн-клавиатурой main из модуля keyboards (kb)
    await message.answer(
        "Выберите необходимую кнопку:",  # Текст сообщения
        reply_markup=kb.main  # Прикрепляем клавиатуру из предварительно созданных
    )


# 2. Общие callback-запросы (без состояний)
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


# 3. Админские команды (без состояний, с проверкой прав)
# Обработчик команды /admin
@router.message(Command("admin"), F.from_user.id.in_(ADMIN_IDS))
async def admin_panel(message: Message):
    await message.answer("Admin panel:", reply_markup=kb.get_admin_kb())


# Временное хранилище для логинов/паролей на одного админа
temp_admin_inputs: dict[int, dict[str, str]] = {}


# 4. Админские callback-запросы (без состояний)
# Нажатие кнопки "Добавить пользователя"
@router.callback_query(F.data == "admin_add_user", F.from_user.id.in_(ADMIN_IDS))
async def start_adding_user(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите логин нового пользователя:")
    temp_admin_inputs[callback.from_user.id] = {}  # Инициализируем словарь
    await state.set_state(AdminStates.waiting_for_new_user)
    await callback.answer()


@router.callback_query(F.data == "admin_remove_user", F.from_user.id.in_(ADMIN_IDS))
async def start_removing_user(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите логин пользователя для удаления:")
    await state.set_state(AdminStates.waiting_for_user_to_remove)
    await callback.answer()


# 5. Обработчики состояний админа (в порядке важности)
@router.message(AdminStates.waiting_for_new_user, F.from_user.id.in_(ADMIN_IDS))
async def handle_admin_add_user(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Если админ начал вводить логин
    if user_id in temp_admin_inputs and "login" not in temp_admin_inputs[user_id]:
        new_user_login = message.text.strip()
        if not new_user_login.endswith("@waveaccess.global"):
            await message.answer("Некорректный логин! Должен быть в формате name@waveaccess.global")
            return  # Выходим из функции, не меняя состояние -> снова запускается обработчик данного состояния

        temp_admin_inputs[user_id]["login"] = new_user_login

        await message.answer("Теперь введите пароль для этого пользователя:")
        return

    # Если ожидается пароль
    if user_id in temp_admin_inputs and "login" in temp_admin_inputs[user_id]:
        login = temp_admin_inputs[user_id]["login"]
        password = message.text.strip()

        # Сохраняем пользователя
        auth_bot.register_user(login, password)  # <-- Здесь твоя функция сохранения

        await message.answer(f"✅ Пользователь \"{login}\" успешно добавлен!")

        # Удаляем временные данные
        del temp_admin_inputs[user_id]

        await message.answer("Готов отвечать на ваши вопросы!")
        await state.set_state(AdminStates.admin)


@router.message(AdminStates.waiting_for_user_to_remove)
async def process_user_removal(message: Message, state: FSMContext):
    login = message.text.strip()

    # Пытаемся удалить пользователя из БД доступа
    remove_data = auth_bot.remove_user(login)  # Эта функция возвращает список tg id для блокировки

    try:
        for _id in remove_data:
            await message.bot.send_message(_id, "❌ Ваш доступ был отозван. Вы больше не "
                                                "можете пользоваться ботом.")
            await message.bot.send_message(_id, "Для разблокировки нажмите команду /start и попробуйте "
                                                "заново авторизоваться")

            storage = SQLiteStorage(db_path=FSM_DB_PATH)
            context = FSMContext(storage, StorageKey(chat_id=_id, user_id=_id, bot_id=message.bot.id))
            print(context)
            await context.set_state(UserStates.banned)
            # await context.

    except Exception as e:
        await message.answer(f"⚠ Не удалось удалить пользователя: {e}")

    await message.answer(f"✅ Пользователь `{login}` удалён.")

    await message.answer("Готов отвечать на ваши вопросы!")
    await state.set_state(AdminStates.admin)


@router.message(AdminStates.login)
async def process_login(message: Message, state: FSMContext):
    await message.answer("Введи пароль админа")
    await state.set_state(AdminStates.password)
    return


@router.message(AdminStates.password)
async def process_login(message: Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await message.answer("Вы успешно вошли как админ!")
        await state.set_state(AdminStates.admin)


# 6. Обработчики состояний пользователей (в порядке workflow)
# Обработчик состояния UserStates.login
# Срабатывает, когда пользователь находится в состоянии "ввода логина"
@router.message(UserStates.login)
async def process_login(message: Message, state: FSMContext):
    # Ниже вставим поиск данного логина (если корректно ввели) в БД доступа
    # Проверяем, что логин заканчивается на "@waveaccess.global" и вообще существует ли
    if not message.text.endswith("@waveaccess.global") or not auth_bot.user_exists(message.text):
        # Если проверка не пройдена - отправляем сообщение об ошибке
        await message.answer("Некорректный (должен быть в формате name@waveaccess.global) или неверный логин!")
        return  # Выходим из функции, не меняя состояние -> снова запускается обработчик данного состояния

    # Сохраняем введенный логин в хранилище FSM
    # Это позволит использовать его на следующем шаге (ввод пароля)
    alphabet = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    p_key = ''.join(secrets.choice(alphabet) for _ in range(10))

    data = await state.update_data(login=message.text, pass_key=p_key)
    print("Данные сохранены:", data)
    stored = await state.get_data()
    print("get_data сразу после обновления:", stored)
    # state_data = await storage.debug_state(StorageKey(chat_id=message.chat.id, user_id=message.from_user.id))
    # print(f"Состояние в БД: {state_data}")
    print(f"Ключ состояния: chat_id={message.chat.id}, user_id={message.from_user.id}, bot_id = {message.bot.id}")

    # Меняем состояние пользователя на UserStates.password
    # Теперь бот будет ожидать ввод пароля
    await state.set_state(UserStates.password)
    print("До get_data в password после смены состояния:", await state.get_data())

    send_key_to_email(message.text, p_key)

    # Отправляем пользователю сообщение с инструкцией
    await message.answer("Отлично! Мы отправили вам на почту одноразовый 10-значный код, скопируйте и вставьте сюда")


# Обработчик состояния ввода пароля (UserStates.password)
# Срабатывает только когда пользователь в состоянии "ввода пароля"
@router.message(UserStates.password)
async def process_password(message: Message, state: FSMContext):
    user_data = await state.get_data()
    print(f"Ключ состояния: chat_id={message.chat.id}, user_id={message.from_user.id}, bot_id = {message.bot.id}")
    print(f"Данные получены: {user_data}")  # ← Отладка
    user_login = user_data.get('login')
    pass_key = user_data.get('pass_key')

    if pass_key != message.text:
        await message.answer("Неверный код! Попробуйте еще раз")
        return

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

    print(message.from_user.id)
    auth_bot.add_session(user_login, message.from_user.id)

    # Отправка сообщения об успешной авторизации
    await message.answer("Вы успешно авторизованы! Можете задавать вопросы!")

    # Меняем состояние - авторизация подтверждена
    await state.set_state(UserStates.auth_confirmed)


async def add_stat(question: str, answer: str, processing_time: float):
    print(f'question = {question}')
    print(f'answer = {answer}')
    print(f'processing_time = {processing_time}')
    pass


async def ask_llm(message: Message):
    # 1. Отправляем сообщение "Обработка запроса..."
    thinking_msg = await message.answer("Обработка запроса...")
    start_time = time.time()  # Засекаем время начала обработки

    try:
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

    await add_stat(message.text, response, processing_time)

    await message.answer("Что вас ещё интересует?)")


@router.message(AdminStates.admin, F.from_user.id.in_(ADMIN_IDS))
async def handle_admin_question(message: Message):
    await ask_llm(message)


# 7. Обработчик для заблокированных пользователей (NEW!)
@router.message(UserStates.banned)  # Или проверка состояния через БД
async def handle_banned_user(message: Message):
    await message.answer("❌ Ваш доступ заблокирован. Попробуйте снова авторизоваться через команду /start. Если "
                         "не удалось - обратитесь к администратору")
    return


@router.message(UserStates.auth_confirmed)
async def handle_user_question(message: Message):
    await ask_llm(message)


# # 1. Стартовые команды (без состояний)
# @router.message(CommandStart())
# @router.message(Command("menu"))
#
# # 2. Общие callback-запросы (без состояний)
# @router.callback_query(F.data == "about_us")
# @router.callback_query(F.data == "about_bot")
# @router.callback_query(F.data == "back_to_main")
# @router.callback_query(F.data == "reauthorisation")
# @router.callback_query(F.data == "help")
#
# # 3. Админские команды (без состояний, с проверкой прав)
# @router.message(Command("admin"), F.from_user.id.in_(ADMIN_IDS))
#
# # 4. Админские callback-запросы (без состояний)
# @router.callback_query(F.data == "admin_add_user"), F.from_user.id.in_(ADMIN_IDS))
# @router.callback_query(F.data == "admin_remove_user"), F.from_user.id.in_(ADMIN_IDS))
#
# # 5. Обработчики состояний админа (в порядке важности)
# @router.message(AdminState.waiting_for_new_user, F.from_user.id.in_(ADMIN_IDS))
# @router.message(AdminState.waiting_for_user_to_remove, F.from_user.id.in_(ADMIN_IDS))
#
# # 6. Обработчики состояний пользователей (в порядке workflow)
# @router.message(UserStates.login)
# @router.message(UserStates.password)
# @router.message(UserStates.auth_confirmed)
#
# # 7. Обработчик для заблокированных пользователей (NEW!)
# @router.message(F.from_user.id.in_(BANNED_USERS))  # Или проверка состояния через БД
# async def handle_banned_user(message: Message):
#     await message.answer("❌ Ваш доступ заблокирован. Обратитесь к администратору.")
#
# # 8. Общий обработчик сообщений (должен быть последним!)
# @router.message()
# async def handle_other_messages(message: Message):
#     await message.answer("Неизвестная команда")
