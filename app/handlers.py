# Основные компоненты aiogram:
# F (фильтры) - для создания гибких условий в обработчиках (например, F.text == "Start"
# Router - основной инструмент для организации обработчиков сообщений (альтернатива Dispatcher в aiogram 3.x)
import asyncio
import logging

# Настройки окружения
import os  # доступ к переменным окружения (os.getenv("TOKEN"))
from dotenv import load_dotenv  # загрузка переменных из .env-файла (для безопасного хранения токенов)

# Кастомные модули
import app.keyboards as kb  # Локальный модуль с клавиатурами
from app.valueai_client import ValueAIClient  # Кастомный клиент для работы с внешним API
from app.auth_valueai import AuthValuai  # Модуль для управления аутентификацией (получение/обновление auth-token)
from config import FSM_DB_PATH
from app.sqlite_storage import SQLiteStorage
from app.email_key import send_key_to_email

from aiogram import F, Router
from aiogram.fsm.storage.base import StorageKey

# Message - класс для работы с текстовыми/медиа-сообщениями
# CallbackQuery - обработка нажатий на инлайн-кнопки
from aiogram.types import Message, CallbackQuery

# CommandStart - фильтр для команды /start
# Command - фильтр для любых команд (например, Command("help"))
from aiogram.filters import CommandStart, Command

from aiogram.fsm.state import State, StatesGroup

# FSMContext - управление состоянием пользователя (установка/получение данных)
from aiogram.fsm.context import FSMContext
from app.issue_statistics import Database

# Работа с датой/временем
from datetime import datetime

import secrets
import string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()  # Создаем экземпляр роутера
load_dotenv('.env')  # Загружаем переменные окружения из файла .env

# Получаем логин и пароль из переменных окружения
VALUEAI_LOGIN = os.getenv("VALUEAI_LOGIN")  # Логин для аутентификации в ValueAI
VALUEAI_PASSWORD = os.getenv("VALUEAI_PASSWORD")  # Пароль для аутентификации в ValueAI

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))

# Создаем менеджер аутентификации, передавая ему полученные учетные данные
auth_manager = AuthValuai(VALUEAI_LOGIN, VALUEAI_PASSWORD)

# Инициализируем клиент для работы с API ValueAI, передавая ему менеджер аутентификации
valueai_client = ValueAIClient(auth_manager)


# Устанавливаем кастомные состояния
class UserStates(StatesGroup):
    start = State()
    login = State()  # Ввод логина
    password = State()  # Ввод пароля
    auth_confirmed = State()  # Успешная авторизация
    banned = State()  # Пользователь больше не авторизован


# Состояния для админа (добавление/удаление пользователя)
class AdminStates(StatesGroup):
    login = State()
    admin = State()
    waiting_for_new_user = State()
    waiting_for_user_to_remove = State()


# 1. Стартовые команды:
# Обработчик команды /start
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(UserStates.start)
    await message.delete()
    await message.answer(
        "Добро пожаловать в HR-чатбот! Перед началом работы необходимо пройти авторизацию",
        reply_markup=kb.start_kb
    )


# Обработчик команды /menu
@router.message(Command("menu"))
async def cmd_help(message: Message):
    # Отправляем сообщение с инлайн-клавиатурой main из модуля keyboards (kb)
    await message.answer(
        "Выберите необходимую кнопку:",  # Текст сообщения
        reply_markup=kb.main_kb  # Прикрепляем клавиатуру из предварительно созданных
    )
    await message.delete()


# Обработчик команды /admin
@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    await asyncio.sleep(1)
    await message.delete()
    data = await state.get_data()
    if data.get('is_admin') == "true":
        await message.answer("Панель админа:", reply_markup=kb.get_admin_kb())
    else:
        await message.answer("Недостаточно прав!")


# 2. Основные callback-запросы:
# Обработчик нажатия на кнопку с callback_data "about_us"
@router.callback_query(F.data == "komands")
async def about_us(callback: CallbackQuery):
    await callback.message.edit_text("/start - команда заново запускает авторизацию в системе\n\n"
                                     "/menu - команда открывает предыдущее меню\n\n"
                                     "/admin - команда открывает кнопки админа", reply_markup=kb.kb_comands)


@router.callback_query(F.data == "close_main_kb")
async def close_commands_handler(callback: CallbackQuery):
    try:
        # Удаляем само сообщение с клавиатурой
        await callback.message.delete()
    except Exception as e:
        # Если сообщение уже удалено или нет прав на удаление
        logger.error(f"Ошибка при удалении сообщения: {e}")

    # Подтверждаем обработку callback (убираем "часики" на кнопке)
    await callback.answer("Клавиатура скрыта")


@router.callback_query(F.data == "close_comands")
async def close_commands_handler(callback: CallbackQuery):
    try:
        # Удаляем само сообщение с клавиатурой
        await callback.message.delete()
    except Exception as e:
        # Если сообщение уже удалено или нет прав на удаление
        logger.error(f"Ошибка при удалении сообщения: {e}")

    # Подтверждаем обработку callback (убираем "часики" на кнопке)
    await callback.answer("Клавиатура скрыта")


@router.callback_query(F.data == "back_to_menu")
async def close_commands_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите необходимую кнопку:",
        reply_markup=kb.main_kb
    )
    await callback.answer()


# 3. Авторизация пользователей:
@router.callback_query(F.data == "sign_in_user")
async def sign_in_user(callback: CallbackQuery, state: FSMContext):
    try:
        # Удаляем само сообщение с клавиатурой
        await callback.message.delete()
    except Exception as e:
        # Если сообщение уже удалено или нет прав на удаление
        logger.error(f"Ошибка при удалении сообщения: {e}")
    await callback.answer()
    await callback.message.answer("Пожалуйста, введите ваш логин в формате name@waveaccess.global")
    await state.set_state(UserStates.login)


# Обработчики состояний пользователей (в порядке workflow)
# Обработчик состояния UserStates.login
# Срабатывает, когда пользователь находится в состоянии "ввода логина"
@router.message(UserStates.login)
async def process_login(message: Message, state: FSMContext, auth_bot: Database):
    # Ниже вставим поиск данного логина (если корректно ввели) в БД доступа
    # Проверяем, что логин заканчивается на "@waveaccess.global" и вообще существует ли
    if not message.text.endswith("@waveaccess.global") or not await auth_bot.login_exists(message.text):
        # Если проверка не пройдена - отправляем сообщение об ошибке
        await message.answer("Некорректный (должен быть в формате name@waveaccess.global) или несуществующий логин!")
        return  # Выходим из функции, не меняя состояние -> снова запускается обработчик данного состояния

    # Сохраняем введенный логин в хранилище FSM
    # Это позволит использовать его на следующем шаге (ввод пароля)
    alphabet = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    p_key = ''.join(secrets.choice(alphabet) for _ in range(10))

    await state.update_data(login=message.text, pass_key=p_key, is_admin="false")

    # Меняем состояние пользователя на UserStates.password
    # Теперь бот будет ожидать ввод пароля
    await state.set_state(UserStates.password)
    # print("До get_data в password после смены состояния:", await state.get_data())

    send_key_to_email(message.text, p_key)

    # Отправляем пользователю сообщение с инструкцией
    await message.answer("Отлично! Мы отправили вам на почту одноразовый 10-значный код, скопируйте и вставьте сюда")


# Обработчик состояния ввода пароля (UserStates.password)
# Срабатывает только когда пользователь в состоянии "ввода пароля"
@router.message(UserStates.password)
async def process_password(message: Message, state: FSMContext, auth_bot: Database):
    user_data = await state.get_data()
    # print(f"Ключ состояния: chat_id={message.chat.id}, user_id={message.from_user.id}, bot_id = {message.bot.id}")
    # print(f"Данные получены: {user_data}")  # ← Отладка
    user_login = user_data.get('login')
    pass_key = user_data.get('pass_key')

    if pass_key != message.text:
        await message.answer("Неверный код! Попробуйте еще раз")
        return

    await auth_bot.add_session(message.from_user.id, user_login)

    # Отправка сообщения об успешной авторизации
    await message.answer("Вы успешно авторизованы! Можете задавать вопросы!")

    # Меняем состояние - авторизация подтверждена
    await state.set_state(UserStates.auth_confirmed)


# 4. Авторизация админов:
@router.callback_query(F.data == "sign_in_admin")
async def sign_in_admin(callback: CallbackQuery, state: FSMContext):
    try:
        # Удаляем само сообщение с клавиатурой
        await callback.message.delete()
    except Exception as e:
        # Если сообщение уже удалено или нет прав на удаление
        logger.error(f"Ошибка при удалении сообщения: {e}")
    await callback.answer()
    await callback.message.answer("Пожалуйста, введите ваш логин в формате name@waveaccess.global")
    await state.set_state(AdminStates.login)


@router.message(AdminStates.login)
async def process_login(message: Message, state: FSMContext, auth_bot: Database):
    if not message.text.endswith("@waveaccess.global") or not await auth_bot.login_exists(message.text):
        # Если проверка не пройдена - отправляем сообщение об ошибке
        await message.answer("Некорректный (должен быть в формате name@waveaccess.global) или несуществующий логин! "
                             "Попробуйте ещё раз или обратитесь к администратору")
        return  # Выходим из функции, не меняя состояние -> снова запускается обработчик данного состояния
    elif not await auth_bot.is_user_admin(message.text, message.from_user.id):
        await message.answer("У вас нет допуска! Попробуйте ещё раз или обратитесь к администратору")
        await state.update_data(is_admin="false")
        return
    await message.answer("Вы успешно вошли как админ!")
    await state.update_data(is_admin="true")
    await message.answer("Готов отвечать на ваши вопросы!")
    await state.set_state(AdminStates.admin)


# 5. Админские функции:
# Нажатие кнопки "Добавить пользователя"
@router.callback_query(F.data == "admin_add_user")
async def start_adding_user(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get('is_admin') == "true":
        await callback.message.edit_text("Введите логин нового пользователя:")
        await state.set_state(AdminStates.waiting_for_new_user)
        await callback.answer()
    else:
        await callback.answer("Недостаточно прав!")


@router.message(AdminStates.waiting_for_new_user)
async def handle_admin_add_user(message: Message, state: FSMContext, auth_bot: Database):
    # Если админ начал вводить логин
    new_user_login = message.text.strip()
    if not new_user_login.endswith("@waveaccess.global"):
        await message.answer("Некорректный логин! Должен быть в формате name@waveaccess.global")
        return  # Выходим из функции, не меняя состояние -> снова запускается обработчик данного состояния

    try:
        await auth_bot.add_login(new_user_login)
        await message.answer(f"✅ Пользователь \"{new_user_login}\" успешно добавлен!")
    except Exception as e:
        logger.error(f'Ошибка добавления нового пользователя: {e}')

    await message.answer("Готов отвечать на ваши вопросы!")
    await state.set_state(AdminStates.admin)


@router.callback_query(F.data == "admin_remove_user")
async def start_removing_user(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get('is_admin') == "true":
        await callback.message.edit_text("Введите логин пользователя для удаления:")
        await state.set_state(AdminStates.waiting_for_user_to_remove)
        await callback.answer()
    else:
        await callback.answer("Недостаточно прав!")


@router.message(AdminStates.waiting_for_user_to_remove)
async def process_user_removal(message: Message, state: FSMContext, auth_bot: Database):
    login = message.text.strip()

    # Пытаемся удалить пользователя из БД доступа
    remove_data = await auth_bot.delete_login_with_tg_ids(login)  # Эта функция возвращает список tg id для блокировки

    try:
        for _id in remove_data:
            await message.bot.send_message(_id, "❌ Ваш доступ был отозван. Вы больше не "
                                                "можете пользоваться ботом")
            await message.bot.send_message(_id, "Для разблокировки нажмите команду /start и попробуйте "
                                                "заново авторизоваться или обратитесь к администратору")

            storage = SQLiteStorage(db_path=FSM_DB_PATH)
            context = FSMContext(storage, StorageKey(chat_id=_id, user_id=_id, bot_id=message.bot.id))
            await context.set_data({})
            await context.set_state(UserStates.banned)

    except Exception as e:
        await message.answer(f"⚠ Не удалось удалить пользователя: {e}")
        logger.error(f"⚠ Не удалось удалить пользователя: {e}")

    await message.answer(f"✅ Пользователь \"{login}\" удалён")

    await message.answer("Готов отвечать на ваши вопросы!")
    await state.set_state(AdminStates.admin)


@router.callback_query(F.data == "close_admin_kb")
async def start_removing_user(callback: CallbackQuery):
    try:
        # Удаляем само сообщение с клавиатурой
        await callback.message.delete()
    except Exception as e:
        # Если сообщение уже удалено или нет прав на удаление
        logger.error(f"Ошибка при удалении сообщения: {e}")

    # Подтверждаем обработку callback (убираем "часики" на кнопке)
    await callback.answer("Клавиатура скрыта")


# 6. Основной workflow:
@router.message(AdminStates.admin)
async def handle_admin_question(message: Message, auth_bot: Database):
    await ask_llm(message, auth_bot)


@router.message(UserStates.auth_confirmed)
async def handle_user_question(message: Message, auth_bot: Database):
    await ask_llm(message, auth_bot)


@router.message(UserStates.banned)  # Или проверка состояния через БД
async def handle_banned_user(message: Message):
    await message.answer("❌ Ваш доступ заблокирован. Попробуйте снова авторизоваться через команду /start. Если "
                         "не удалось - обратитесь к администратору")
    return


# 7. Вспомогательные состояния:
@router.message(UserStates.start)
async def process_start(message: Message):
    answer_message = await message.answer("Авторизуйтесь!")
    await asyncio.sleep(1)
    await answer_message.delete()
    await message.delete()


# 8. Взаимодействие с LLM:
async def ask_llm(message: Message, auth_bot: Database):
    # Инициализация таймеров
    timers = {
        'total_start': datetime.now(),
        'thinking_msg': None,
        'llm_request': None,
        'response_processing': None,
        'cleanup': None,
        'final_response': None,
        'sending_response': None,
        'statistics': None
    }

    # 1. Отправляем сообщение "Обработка запроса..."
    thinking_msg = await message.answer("Обработка запроса...")
    timers['thinking_msg'] = datetime.now()

    kod = 0
    try:
        # 2. Отправляем запрос к ИИ-ассистенту
        timers['llm_request_start'] = datetime.now()
        response = await valueai_client.send_message_to_llm(message.text)
        timers['llm_request_end'] = datetime.now()

        # 3. Очищаем ответ от технической информации
        timers['response_processing_start'] = datetime.now()
        response = response.split('**********', 1)[0].strip()

        if response.startswith("Код ответа — 200"):
            kod = 200
            response = response.replace("Код ответа — 200", "").strip()
        else:
            kod = 100
            response = response.replace("Код ответа — 100", "").strip()
        timers['response_processing_end'] = datetime.now()

        print(f'код ответа = {kod}')

        # 4. Проверяем, что ответ не пустой
        if not response:
            logger.info("Пустой ответ от ИИ")
            response = (
                "Извините, не удалось обработать ваш запрос. "
                "Попробуйте переформулировать вопрос или обратитесь позже"
            )

    except Exception as e:
        # 5. Логируем ошибку
        logger.error(f"Ошибка обработки сообщения: {e}")

        # 6. Формируем запасной вариант ответа
        response = (
            "Извините, не удалось обработать ваш запрос. "
            "Попробуйте переформулировать вопрос или обратитесь позже"
        )

    # 7. Удаляем сообщение "Обработка запроса..."
    timers['cleanup_start'] = datetime.now()
    await thinking_msg.delete()
    timers['cleanup_end'] = datetime.now()

    # 8. Формируем финальное сообщение
    timers['final_response_start'] = datetime.now()
    processing_time = round((datetime.now() - timers['total_start']).total_seconds(), 2)
    final_response = (
        f"{response}\n\n"
        f"⏱ Время обработки: {processing_time} сек."
    )
    timers['final_response_end'] = datetime.now()

    # 9. Отправляем ответ пользователю
    timers['sending_response_start'] = datetime.now()
    await message.answer(text=final_response)
    timers['sending_response_end'] = datetime.now()

    # 10. Рассчитываем время выполнения
    timers['total_end'] = datetime.now()

    # Вычисляем временные интервалы
    total_time = round((timers['total_end'] - timers['total_start']).total_seconds(), 2)
    llm_request_time = round((timers['llm_request_end'] - timers['llm_request_start']).total_seconds(), 2)
    response_processing_time = round(
        (timers['response_processing_end'] - timers['response_processing_start']).total_seconds(), 2)
    cleanup_time = round((timers['cleanup_end'] - timers['cleanup_start']).total_seconds(), 2)
    final_response_time = round((timers['final_response_end'] - timers['final_response_start']).total_seconds(), 2)
    sending_response_time = round((timers['sending_response_end'] - timers['sending_response_start']).total_seconds(),
                                  2)

    # Логируем временные метки
    logger.debug(
        "\n=== Профилирование времени выполнения (ask llm) ==="
        f"1. Отправка thinking сообщения:"
        f" {round((timers['thinking_msg'] - timers['total_start']).total_seconds(), 2)} сек."
        f"2. Запрос к LLM: {llm_request_time} сек. ({llm_request_time / total_time * 100:.1f}%)"
        f"3. Обработка ответа: {response_processing_time} сек."
        f"4. Удаление thinking сообщения: {cleanup_time} сек."
        f"5. Формирование финального ответа: {final_response_time} сек."
        f"6. Отправка ответа пользователю: {sending_response_time} сек."
        f"7. Общее время выполнения: {total_time} сек."
        "=====================================")

    # Запись статистики
    timers['statistics_start'] = datetime.now()
    if kod == 200:
        await auth_bot.save_statistics(message.text, response, processing_time)

    timers['statistics_end'] = datetime.now()

    statistics_time = round((timers['statistics_end'] - timers['statistics_start']).total_seconds(), 2)
    logger.debug(f"8. Запись статистики: {statistics_time} сек.")

    await message.answer("Что вас ещё интересует?)")
