# Основные компоненты aiogram:
# F (фильтры) - для создания гибких условий в обработчиках (например, F.text == "Start"
# Router - основной инструмент для организации обработчиков сообщений (альтернатива Dispatcher в aiogram 3.x)
from aiogram import F, Router
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
from datetime import datetime

# Для логирования ошибок
import logger

# Настройки окружения
import os  # доступ к переменным окружения (os.getenv("TOKEN"))
from dotenv import load_dotenv  # загрузка переменных из .env-файла (для безопасного хранения токенов)

# Кастомные модули
import app.keyboards as kb  # Локальный модуль с клавиатурами
from app.storage import user_storage, UserData  # user_storage - ваше хранилище данных пользователей
# UserData - класс для хранения данных пользователя
from app.valueai_client import ValueAIClient  # Кастомный клиент для работы с внешним API
from app.auth_manager import AuthManager  # Модуль для управления аутентификацией (получение/обновление auth-token)

router = Router()  # Создаем экземпляр роутера
load_dotenv('.env')  # Загружаем переменные окружения из файла .env

# Получаем логин и пароль из переменных окружения
VALUEAI_LOGIN = os.getenv("VALUEAI_LOGIN")  # Логин для аутентификации в ValueAI
VALUEAI_PASSWORD = os.getenv("VALUEAI_PASSWORD")  # Пароль для аутентификации в ValueAI

# Создаем менеджер аутентификации, передавая ему полученные учетные данные
auth_manager = AuthManager(VALUEAI_LOGIN, VALUEAI_PASSWORD)

# Инициализируем клиент для работы с API ValueAI, передавая ему менеджер аутентификации
valueai_client = ValueAIClient(auth_manager)


# Устанавливаем кастомные состояния
class UserStates(StatesGroup):
    login = State()
    password = State()


# Обработчик команды /start
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
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
    if not message.text.endswith("@waveaccess.global"):  # Проверяем, что логин заканчивается на "@waveaccess.global"
        # Если проверка не пройдена - отправляем сообщение об ошибке
        await message.answer("Некорректный логин! Должен быть в формате name@waveaccess.global")
        return  # Выходим из функции, не меняя состояние -> снова запускается обработчик данного состояния

    # Сохраняем введенный логин в хранилище FSM
    # Это позволит использовать его на следующем шаге (ввод пароля)
    await state.update_data(login=message.text)

    # Меняем состояние пользователя на UserStates.password
    # Теперь бот будет ожидать ввод пароля
    await state.set_state(UserStates.password)

    # Отправляем пользователю сообщение с инструкцией
    await message.answer("Теперь введите ваш пароль:")


# Обработчик состояния ввода пароля (UserStates.password)
# Срабатывает только когда пользователь в состоянии "ввода пароля"
@router.message(UserStates.password)
async def process_password(message: Message, state: FSMContext):
    if not message.text:  # Проверка что пароль не пустой (вот здесь вставим логику проверки пароля для данного логина)
        await message.answer("Неверный пароль! Попробуйте еще раз.")  # Отправка сообщения об ошибке если пароль пустой
        return  # Выход из функции без изменения состояния

    # Создание нового объекта данных пользователя
    user_data = UserData()

    # Фиксация времени последней успешной авторизации
    user_data.last_auth = datetime.now()  # Текущее время

    # Сохранение данных пользователя в хранилище
    # Ключ - ID пользователя Telegram (message.from_user.id)
    user_storage[message.from_user.id] = user_data  # сохраняем

    # Очистка состояния FSM (выход из цепочки авторизации)
    await state.clear()

    # Отправка сообщения об успешной авторизации
    await message.answer("Вы успешно авторизованы! Срок действия авторизации - 7 дней.")


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


@router.message()
async def handle_user_message(message: Message):
    """
    Обработчик всех текстовых сообщений, не попавших в другие обработчики.
    Отправляет запрос к ИИ-модели и возвращает ответ пользователю.
    """
    try:
        # 1. Отправляем запрос к ИИ-ассистенту
        response = await valueai_client.send_message_to_llm(message.text)

        # 2. Очищаем ответ от технической информации (все после ******)
        response = response.split('**********', 1)[0].strip()

        # 3. Проверяем, что ответ не пустой
        if not response:
            raise ValueError("Пустой ответ от ИИ")

    except Exception as e:
        # Логируем ошибку для дальнейшего анализа
        logger.error(f"Ошибка обработки сообщения: {e}", message)

        # Формируем запасной вариант ответа
        response = (
            "Извините, не удалось обработать ваш запрос. "
            "Попробуйте переформулировать вопрос или обратитесь позже."
        )

    # 4. Отправляем ответ пользователю
    await message.answer(text=response)
