# Необходимые классы для создания инлайн-клавиатур из aiogram
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton)

start_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text="Войти как пользователь",
            callback_data="sign_in_user"
        )],
        [InlineKeyboardButton(
            text="Войти как админ",
            callback_data="sign_in_admin"
        )]
    ]
)

# Создание основной инлайн-клавиатуры (main)
main_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        # Первый ряд - кнопка с внешней ссылкой
        [InlineKeyboardButton(
            text='О компании',
            url='https://www.waveaccess.ru/'  # Внешний URL вместо callback_data
        )],

        # Второй ряд - обычная callback-кнопка
        [InlineKeyboardButton(
            text='Документация бота',
            url='https://disk.yandex.ru/i/DcN71l1uadi3cA'
        )],

        # Третий ряд - кнопка возврата
        [InlineKeyboardButton(
            text='Чё-то ещё надо вставить',  # Эмодзи для лучшей визуализации
            callback_data='something_else'  # Обработчик вернет в главное меню
        )]
    ]
)


def get_admin_kb():
    buttons = [
        [InlineKeyboardButton(text="Add user", callback_data="admin_add_user")],
        [InlineKeyboardButton(text="Remove user", callback_data="admin_remove_user")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
