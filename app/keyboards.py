# Необходимые классы для создания инлайн-клавиатур из aiogram
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton)

# Создание основной инлайн-клавиатуры (main)
main = InlineKeyboardMarkup(
    inline_keyboard=[
        # Первый ряд кнопок (массив с одной кнопкой)
        [InlineKeyboardButton(
            text="Re-authorization",  # Текст на кнопке
            callback_data="reauthorisation"  # Данные, которые вернутся при нажатии
        )],

        # Второй ряд кнопок
        [InlineKeyboardButton(
            text="About us",
            callback_data="about_us"
        )],

        # Третий ряд кнопок
        [InlineKeyboardButton(
            text="Help",
            callback_data="help"
        )]
    ]
)

# Создание инлайн-клавиатуры "О нас" (about_us)
about_us = InlineKeyboardMarkup(
    inline_keyboard=[
        # Первый ряд - кнопка с внешней ссылкой
        [InlineKeyboardButton(
            text='About company',
            url='https://www.waveaccess.ru/'  # Внешний URL вместо callback_data
        )],

        # Второй ряд - обычная callback-кнопка
        [InlineKeyboardButton(
            text='About bot',
            callback_data='about_bot'
        )],

        # Третий ряд - кнопка возврата
        [InlineKeyboardButton(
            text='🔙 Back',  # Эмодзи для лучшей визуализации
            callback_data='back_to_main'  # Обработчик вернет в главное меню
        )]
    ]
)