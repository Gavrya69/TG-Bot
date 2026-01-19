import os
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.exceptions import TelegramNetworkError

from services.downloader import download_youtube, download_tiktok

router = Router()

@router.callback_query(F.data =='dl_no')
async def cancel_download(callback: CallbackQuery):
    
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data.startswith('dl_yes'))
async def start_download(callback: CallbackQuery):
    await callback.message.edit_text('Downloading...')
    await callback.answer()
    
    platform = callback.data.split(':')[1]
    url = callback.message.reply_to_message.text
    loop = asyncio.get_running_loop()
    if platform == 'yt':
        filename = await loop.run_in_executor(None, download_youtube, url)
    elif platform == 'tt':
        filename = await loop.run_in_executor(None, download_tiktok, url)
    else:
        await callback.message.edit_text('Unknown platform')
        return
    
    if not filename:
        await callback.message.edit_text('Error')
        await callback.answer()
        return
    
    await callback.message.edit_text('Sending...')

    try:
        await callback.message.answer_video(
            video=FSInputFile(filename),
            caption='Your video',
            request_timeout=180
        )
    except TelegramNetworkError:
        await callback.message.edit_text('Exception TelegramNetworkError')
        await callback.answer()
        
    os.remove(filename)
    await callback.message.delete()
    
