from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime

import app.keyboards as kb
from app.storage import user_storage, UserData

router = Router()


class UserStates(StatesGroup):
    login = State()
    password = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(UserStates.login)
    await message.answer(
        "Добро пожаловать в HR-чатбот!\n\n"
        "Пожалуйста, введите ваш логин в формате name@waveaccess.global"
    )


@router.message(UserStates.login)
async def process_login(message: Message, state: FSMContext):
    if not message.text.endswith("@waveaccess.global"):
        await message.answer("Некорректный логин! Должен быть в формате name@waveaccess.global")
        return

    await state.update_data(login=message.text)
    await state.set_state(UserStates.password)
    await message.answer("Теперь введите ваш пароль:")


@router.message(UserStates.password)
async def process_password(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Неверный пароль! Попробуйте еще раз.")
        return

    user_data = UserData()
    user_data.last_auth = datetime.now()  # Фиксируем время авторизации
    user_storage[message.from_user.id] = user_data  # сохраняем

    await state.clear()
    await message.answer("Вы успешно авторизованы! Срок действия авторизации - 7 дней.")


@router.message(Command("menu"))
async def cmd_help(message: Message, state: FSMContext):
    await message.answer("Выберите необходимую кнопку:", reply_markup=kb.main)


@router.callback_query(F.data == "about_us")
async def about_us(callback: CallbackQuery):
    await callback.message.edit_text("Выберите раздел:", reply_markup=kb.about_us)
    await callback.answer()


@router.callback_query(F.data == "about_bot")
async def about_bot(callback: CallbackQuery):
    await callback.answer(
        "Это HR-чатбот компании WaveAccess.\n"
        "Я могу ответить на ваши вопросы о работе в компании.",
        show_alert=True  # Это создаст всплывающее окно
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Вы вернулись в главное меню.",
        reply_markup=kb.main
    )
    await callback.answer()


@router.callback_query(F.data == "reautorisation")
async def reautorisation(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.login)
    await callback.answer()  # Обязательно, чтобы Telegram "убрал часики"

    await callback.message.answer(
        "Пожалуйста, введите ваш логин в формате name@waveaccess.global:"
    )


@router.callback_query(F.data == "help")
async def about_bot(callback: CallbackQuery):
    await callback.answer(
        "Повторная авторизация нужна на случай, если ваши данные устарели",
        show_alert=True  # Это создаст всплывающее окно
    )


@router.message()
async def handle_user_message(message: Message):

    # Обработка вопроса (заглушка)
    response = "Я пока не знаю ответ на этот вопрос..."

    # Отправляем ответ с обновленной клавиатурой
    await message.answer(response)
