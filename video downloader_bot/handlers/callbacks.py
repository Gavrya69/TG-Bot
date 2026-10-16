import asyncio
import logging
import os
from functools import partial

from aiogram import F, Router
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import CallbackQuery, FSInputFile

from services.cookies import is_cookies_fresh, reason_to_user_message
from services.downloader import (
    AUDIO_BITRATE,
    SelectStatus,
    download_audio,
    download_video,
    select_audio_info,
    select_video_format,
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


def _cookies_need_update_text(reason: str) -> str:
    return (
        f"Не удалось скачать.\n"
        f"{reason_to_user_message(reason)}\n\n"
        "Обнови cookies: напиши боту в ЛС /load_cookies и пришли файл cookies.txt"
    )


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

    selected_format, status = await loop.run_in_executor(
        None,
        partial(select_video_format, url, platform, use_cookies=False),
    )
    use_cookies = False

    if status == SelectStatus.FAILED and platform == "yt":
        ok, reason = is_cookies_fresh()
        if not ok:
            logger.warning("Video select failed and cookies not fresh (%s): %s", reason, url)
            await callback.message.edit_text(_cookies_need_update_text(reason))
            return

        await callback.message.edit_text(
            "Обычная загрузка не удалась.\nНачинаю скачивание через cookies..."
        )
        selected_format, status = await loop.run_in_executor(
            None,
            partial(select_video_format, url, platform, use_cookies=True),
        )
        use_cookies = True

    if status == SelectStatus.TOO_LARGE or selected_format is None:
        logger.warning("Video download is not possible (%s): %s", status, url)
        await callback.message.edit_text("Video download is not possible")
        return

    file_resolution = selected_format.get("resolution") or "unknown resolution"

    logger.debug(
        "Downloading video (%s, cookies=%s): %s",
        file_resolution,
        use_cookies,
        url,
    )
    await callback.message.edit_text(f"Downloading video...\n{file_resolution}")

    filename = await loop.run_in_executor(
        None,
        partial(download_video, url, selected_format, platform, use_cookies=use_cookies),
    )

    # Select worked without cookies, but download failed — retry with cookies once.
    if not filename and platform == "yt" and not use_cookies:
        ok, reason = is_cookies_fresh()
        if ok:
            await callback.message.edit_text(
                "Обычная загрузка не удалась.\nНачинаю скачивание через cookies..."
            )
            selected_format, status = await loop.run_in_executor(
                None,
                partial(select_video_format, url, platform, use_cookies=True),
            )
            if selected_format is not None and status == SelectStatus.OK:
                file_resolution = selected_format.get("resolution") or file_resolution
                filename = await loop.run_in_executor(
                    None,
                    partial(
                        download_video,
                        url,
                        selected_format,
                        platform,
                        use_cookies=True,
                    ),
                )
                use_cookies = True
        else:
            await callback.message.edit_text(_cookies_need_update_text(reason))
            return

    if not filename:
        if use_cookies:
            await callback.message.edit_text(_cookies_need_update_text("session_expired"))
        else:
            await callback.message.edit_text("Video download error")
        return

    await callback.message.edit_text("Sending video...")

    vcodec = selected_format.get("vcodec") or ""
    caption = f"Your video ({file_resolution})"
    if vcodec:
        caption = f"{caption}\n{vcodec}"
    # Telegram plays H.264 inline. AV1 and VP9 are sent as a file so the pixels stay intact.
    send_as_file = not vcodec.startswith("avc")

    try:
        if send_as_file:
            await callback.message.answer_document(
                document=FSInputFile(filename),
                caption=caption,
                request_timeout=180,
            )
        else:
            await callback.message.answer_video(
                video=FSInputFile(filename),
                caption=caption,
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

    audio_info, status = await loop.run_in_executor(
        None,
        partial(select_audio_info, url, platform, use_cookies=False),
    )
    use_cookies = False

    if status == SelectStatus.FAILED and platform == "yt":
        ok, reason = is_cookies_fresh()
        if not ok:
            logger.warning("Audio select failed and cookies not fresh (%s): %s", reason, url)
            await callback.message.edit_text(_cookies_need_update_text(reason))
            return

        await callback.message.edit_text(
            "Обычная загрузка не удалась.\nНачинаю скачивание через cookies..."
        )
        audio_info, status = await loop.run_in_executor(
            None,
            partial(select_audio_info, url, platform, use_cookies=True),
        )
        use_cookies = True

    if status == SelectStatus.TOO_LARGE or audio_info is None:
        logger.warning("Audio download is not possible (%s): %s", status, url)
        await callback.message.edit_text("Audio download is not possible")
        return

    audio_desc = format_audio_desc(audio_info)

    await callback.message.edit_text(
        f"Downloading audio...\nSource: {audio_desc}\nOutput: mp3"
    )

    filename = await loop.run_in_executor(
        None,
        partial(download_audio, url, platform, use_cookies=use_cookies),
    )

    if not filename and platform == "yt" and not use_cookies:
        ok, reason = is_cookies_fresh()
        if ok:
            await callback.message.edit_text(
                "Обычная загрузка не удалась.\nНачинаю скачивание через cookies..."
            )
            audio_info, status = await loop.run_in_executor(
                None,
                partial(select_audio_info, url, platform, use_cookies=True),
            )
            if audio_info is not None and status == SelectStatus.OK:
                audio_desc = format_audio_desc(audio_info)
                filename = await loop.run_in_executor(
                    None,
                    partial(download_audio, url, platform, use_cookies=True),
                )
                use_cookies = True
        else:
            await callback.message.edit_text(_cookies_need_update_text(reason))
            return

    if not filename:
        if use_cookies:
            await callback.message.edit_text(_cookies_need_update_text("session_expired"))
        else:
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
