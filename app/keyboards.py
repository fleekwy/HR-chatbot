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
        [InlineKeyboardButton(
            text='О компании',
            url='https://www.waveaccess.ru/'
        )],
        [InlineKeyboardButton(
            text='Документация бота',
            url='https://disk.yandex.ru/i/2jeRKxtSZYybug'
        )],
        [InlineKeyboardButton(
            text='Команды бота',
            callback_data='komands'
        )],
        [InlineKeyboardButton(
            text='Закрыть',
            callback_data='close_main_kb'
        )]
    ]
)

kb_comands = InlineKeyboardMarkup(
    inline_keyboard=[
        # Первый ряд - кнопка с внешней ссылкой
        [InlineKeyboardButton(
            text='Закрыть',
            callback_data="close_comands"  # Внешний URL вместо callback_data
        )],

        # Второй ряд - обычная callback-кнопка
        [InlineKeyboardButton(
            text='Назад',
            callback_data='back_to_menu'
        )]
    ]
)


def get_admin_kb():
    buttons = [
        [InlineKeyboardButton(text="Добавить пользователя", callback_data="admin_add_user")],
        [InlineKeyboardButton(text="Удалить пользователя", callback_data="admin_remove_user")],
        [InlineKeyboardButton(text='Закрыть', callback_data='close_admin_kb')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
