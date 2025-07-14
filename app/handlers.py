from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.keyboards as kb

router = Router()

class Register(StatesGroup):
    number = State()

class Authentification(StatesGroup):
    login = State()
    password = State()


@router.message(CommandStart())  # декоратор
async def cmd_start(message: Message):  # асинхронная функция, на вход которой подаётся сообщение
    await message.answer('Hello!')
    await message.answer('I`m happy to see you! This is HR-chatbot, that can answer on your working* questions!\n\n'
                        'But before this you need to go throw the authentication. '
                        'Please give your WaveAccess-corporative login and password: ')

@router.message(Command('authentification'))
async def authentification(message: Message, state: FSMContext):
    await state.set_state((Authentification.login))
    await message.answer('Введите логин вида ***@waveaccess.global: ', reply_markup=kb.main)


@router.message(Authentification.login)
async def authentification_login(message: Message, state: FSMContext):
    await state.update_data(login=message.text)
    await state.set_state(Authentification.password)
    await message.answer('Введите свой пароль:')


@router.message(Authentification.password)
async def authentification_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    data = await state.get_data()
    await message.answer(f'Ваш логин: {data["login"]}\nВаш пароль: {data["password"]}')
    await state.clear()


@router.message(Command('register'))
async def register(message: Message, state: FSMContext):
    await state.set_state((Register.number))
    await message.answer('Отправьте ваш номер телефона', reply_markup=kb.get_number)

@router.message(Register.number, F.contact)
async def register_number(message: Message, state: FSMContext):
    await state.update_data(number=message.contact.phone_number)
    data = await state.get_data()
    await message.answer(f'Ваш номер: {data["number"]}')
    await state.clear()


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Вы нажали на кнопку помощи')


@router.message(F.text == 'О нас')
async def about_us(message: Message):
    await message.answer('Выберите, какая информация интересует', reply_markup=kb.about_us)


@router.callback_query(F.data=='company')
async def company(callback: CallbackQuery):
    await callback.answer('Вы выбрали "О компании"')
    await callback.message.answer('WaveAccess - современная IT-компания, занимающаяся разработков ПО на заказ с '
                                  'использованием ML!')

@router.callback_query(F.data=='bot')
async def bot(callback: CallbackQuery):
    await callback.answer('Вы выбрали "О боте"', show_alert=False)
    await callback.message.answer('Это умный HR-чатбот, который отвечает на рабочие вопросы сотрудников компании '
                                  'WaveAccess!')