import re
from aiogram import Router
from aiogram.types import Message

from keyboards.download import download_keyboard

router = Router()

URL_RE = re.compile(r"(https?://\S+)", re.IGNORECASE)

@router.message()
async def detect_link(message: Message):
    if not message.text:
        return

    match = URL_RE.search(message.text)
    if not match:
        return

    url = match.group(0)

    await message.reply(
        'Опа, фиксируем?',
        reply_markup=download_keyboard(url)
    )
