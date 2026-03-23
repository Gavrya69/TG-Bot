import asyncio
import logging
import os

from aiogram import F, Router
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import CallbackQuery, FSInputFile

from services.downloader import download_video, select_format

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "dl_no")
async def cancel_download(callback: CallbackQuery) -> None:

    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("dl_yes"))
async def start_download(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text("Checking video...")

    platform = callback.data.split(":")[1]
    url = callback.message.reply_to_message.text
    loop = asyncio.get_running_loop()

    if platform in ("yt", "tt"):
        selected_format = await loop.run_in_executor(None, select_format, url, platform)
    else:
        logger.warning("Unkown platform: %s", url)
        await callback.message.edit_text("Unknown platform")
        return

    if selected_format is None:
        logger.warning("Downloading is not possible: %s", url)
        await callback.message.edit_text("Downloading is not possible")
        return

    file_size = (selected_format.get("filesize") or selected_format.get("filesize_approx")) / 1024 / 1024
    file_resolution = selected_format.get("resolution")
    logger.debug("Downloading file %.3f mb (%sp): %s", file_size, file_resolution, url)
    await callback.message.edit_text(f"Downloading...\n{file_size:.3} mb ({file_resolution}p)")

    filename = await loop.run_in_executor(None, download_video, url, selected_format, platform)

    if not filename:
        await callback.message.edit_text("Error")
        return

    logger.debug("Sending file %.3f mb (%sp): %s", file_size, file_resolution, filename)
    await callback.message.edit_text("Sending...")

    try:
        with open(filename, "rb") as f:
            await callback.message.answer_video(
                video=FSInputFile(filename),
                caption=f"Your video ({file_resolution})",
                request_timeout=180,
            )
        logger.debug("Successfully sended file %.3f mb (%sp): %s", file_size, file_resolution, filename)

    except TelegramNetworkError:
        logger.exception("Failed to send video: %s", filename)
        await callback.message.edit_text("Failed to send video")

    finally:
        os.remove(filename)
        logger.debug("Removed file: %s", filename)
        await callback.message.delete()
