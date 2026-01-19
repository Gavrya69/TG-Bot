import re
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

URL_RE = re.compile(
    r'(https?://(?:www\.)?'
    r'(?:'
        r'youtube\.com/(?:watch\?v=|shorts/)|'
        r'youtu\.be/|'
        r'tiktok\.com/@[\w\.-]+/video/' 
    r')'
    r'[^\s]+)',
    re.IGNORECASE
)

@router.message()
async def detect_link(message: Message):
    if not message.text:
        return

    match = URL_RE.search(message.text)
    if not match:
        return

    url = match.group(0)
    
    await message.reply(
        'Download?',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Yes',
                        callback_data=f'dl_yes'
                    ),
                    InlineKeyboardButton(
                        text='No',
                        callback_data='dl_no'
                    ),
                ]
            ]
        ))
