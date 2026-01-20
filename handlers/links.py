import re
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

YOUTUBE_RE = re.compile(
    r'(https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)[^\s]+)',
    re.IGNORECASE
)

TIKTOK_RE = re.compile(
    r'(https?://(?:www\.)?tiktok\.com/@[\w\.-]+/video/\d+)',
    re.IGNORECASE
)

@router.message()
async def detect_link(message: Message):
    if not message.text:
        return
    
    yt = YOUTUBE_RE.search(message.text)
    tt = TIKTOK_RE.search(message.text)

    if yt:
        url = yt.group(0)
        platform = 'yt'
    elif tt:
        url = tt.group(0)
        platform = 'tt'
    else:
        return
    
    print(f'[{__name__}] Detected link: {message.text}')
    await message.reply(
        'Download?',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Yes',
                        callback_data=f'dl_yes:{platform}'
                    ),
                    InlineKeyboardButton(
                        text='No',
                        callback_data='dl_no'
                    ),
                ]
            ]
        ))
