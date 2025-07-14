from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)

main = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Очистить чат')],
                                     [KeyboardButton(text='История поиска')],
                                     [KeyboardButton(text='Контакты'),
                                      KeyboardButton(text='О нас')]],
                           resize_keyboard=True,
                           input_field_placeholder='Выберите пункт меню...')

about_us = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='О компании', callback_data='company')],
    [InlineKeyboardButton(text='О боте', callback_data='bot')]
    ]
)


get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отправить номер телефона', request_contact=True)]],
                                 resize_keyboard=True)
