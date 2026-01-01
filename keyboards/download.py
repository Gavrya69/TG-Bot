from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def download_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Да',
                    callback_data=f'download:{url}'
                ),
                InlineKeyboardButton(
                    text='Нет',
                    callback_data='cancel'
                ),
            ]
        ]
    )
