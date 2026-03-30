import asyncio
import logging
import os

from aiogram import F, Router
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import CallbackQuery, FSInputFile

from services.downloader import (
    download_audio,
    download_video,
    select_audio_info,
    select_video_format,
    AUDIO_BITRATE
)

router = Router()
logger = logging.getLogger(__name__)


def format_audio_desc(audio_info: dict) -> str:
    ext = audio_info.get("audio_ext") or audio_info.get("ext")
    abr = audio_info.get("abr")
    acodec = audio_info.get("acodec")

    parts = []

    if ext and ext != "none":
        parts.append(ext)

    if abr:
        if isinstance(abr, (int, float)):
            parts.append(f"{abr:.0f} kbps")
        else:
            parts.append(f"{abr} kbps")

    if acodec and acodec != "none":
        parts.append(acodec)

    return ", ".join(parts) if parts else "best available audio"


@router.callback_query(F.data == "dl_cancel")
async def cancel_download(callback: CallbackQuery) -> None:
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("dl_video:"))
async def start_video_download(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text("Checking video...")

    platform = callback.data.split(":")[1]
    url = callback.message.reply_to_message.text
    loop = asyncio.get_running_loop()

    if platform not in ("yt", "tt"):
        logger.warning("Unknown platform: %s", url)
        await callback.message.edit_text("Unknown platform")
        return

    selected_format = await loop.run_in_executor(None, select_video_format, url, platform)

    if selected_format is None:
        logger.warning("Video download is not possible: %s", url)
        await callback.message.edit_text("Video download is not possible")
        return

    file_resolution = selected_format.get("resolution") or "unknown resolution"

    logger.debug("Downloading video (%s): %s", file_resolution, url)
    await callback.message.edit_text(f"Downloading video...\n{file_resolution}")

    filename = await loop.run_in_executor(None, download_video, url, selected_format, platform)

    if not filename:
        await callback.message.edit_text("Video download error")
        return

    await callback.message.edit_text("Sending video...")

    try:
        await callback.message.answer_video(
            video=FSInputFile(filename),
            caption=f"Your video ({file_resolution})",
            request_timeout=180,
        )
        logger.debug("Successfully sent video: %s", filename)

    except TelegramNetworkError:
        logger.exception("Failed to send video: %s", filename)
        await callback.message.edit_text("Failed to send video")

    finally:
        if os.path.exists(filename):
            os.remove(filename)
            logger.debug("Removed file: %s", filename)

    await callback.message.delete()


@router.callback_query(F.data.startswith("dl_audio:"))
async def start_audio_download(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text("Checking audio...")

    platform = callback.data.split(":")[1]
    url = callback.message.reply_to_message.text
    loop = asyncio.get_running_loop()

    if platform not in ("yt", "tt"):
        logger.warning("Unknown platform: %s", url)
        await callback.message.edit_text("Unknown platform")
        return

    audio_info = await loop.run_in_executor(None, select_audio_info, url, platform)

    if audio_info is None:
        logger.warning("Audio download is not possible: %s", url)
        await callback.message.edit_text("Audio download is not possible")
        return

    audio_desc = format_audio_desc(audio_info)

    await callback.message.edit_text(
        f"Downloading audio...\nSource: {audio_desc}\nOutput: mp3"
    )

    filename = await loop.run_in_executor(None, download_audio, url, platform)

    if not filename:
        await callback.message.edit_text("Audio download error")
        return

    await callback.message.edit_text("Sending audio...")

    try:
        await callback.message.answer_audio(
            audio=FSInputFile(filename),
            caption=f"Source: {audio_desc}\nOutput: mp3, {AUDIO_BITRATE} kbps",
            request_timeout=180,
        )
        logger.debug("Successfully sent audio: %s", filename)

    except TelegramNetworkError:
        logger.exception("Failed to send audio: %s", filename)
        await callback.message.edit_text("Failed to send audio")

    finally:
        if os.path.exists(filename):
            os.remove(filename)
            logger.debug("Removed file: %s", filename)

    await callback.message.delete()