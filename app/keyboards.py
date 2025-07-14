from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)


main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Повторная авторизация", callback_data="reautorisation")],
    [InlineKeyboardButton(text="О нас", callback_data="about_us")],
    [InlineKeyboardButton(text="Помощь", callback_data="help")]
])


about_us = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='О компании', url='https://www.waveaccess.ru/')],
    [InlineKeyboardButton(text='О боте', callback_data='about_bot')],
    [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')]]
)