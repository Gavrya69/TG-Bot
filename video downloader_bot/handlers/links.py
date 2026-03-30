import logging
import re

from aiogram import Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

router = Router()
logger = logging.getLogger(__name__)

YOUTUBE_RE = re.compile(
    r"(https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)[^\s]+)",
    re.IGNORECASE,
)

TIKTOK_RE = re.compile(
    r"(https?://(?:www\.)?tiktok\.com/@[\w\.-]+/video/\d+)",
    re.IGNORECASE,
)


@router.message()
async def detect_link(message: Message) -> None:
    if not message.text:
        return

    yt = YOUTUBE_RE.search(message.text)
    tt = TIKTOK_RE.search(message.text)

    if yt:
        url = yt.group(0)
        platform = "yt"
    elif tt:
        url = tt.group(0)
        platform = "tt"
    else:
        return

    logger.debug("Detected link: %s", url)

    await message.reply(
        "Choose format:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="MP3",
                        callback_data=f"dl_audio:{platform}",
                    ),
                    InlineKeyboardButton(
                        text="MP4",
                        callback_data=f"dl_video:{platform}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Cancel",
                        callback_data="dl_cancel",
                    ),
                ],
            ],
        ),
    )