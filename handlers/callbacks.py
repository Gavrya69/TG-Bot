import os
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.exceptions import TelegramNetworkError

from services.downloader import download_youtube

router = Router()

@router.callback_query(F.data =='dl_no')
async def cancel_download(callback: CallbackQuery):
    
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data =='dl_yes')
async def start_download(callback: CallbackQuery):
    await callback.message.edit_text('Ща скачаю погодь...')
    await callback.answer()
    
    loop = asyncio.get_running_loop()
    filename = await loop.run_in_executor(
        None,
        download_youtube,
        callback.message.reply_to_message.text
    )
    
    if not filename:
        await callback.message.edit_text('Чот не вышло нихуя(')
        await callback.answer()
        return
    
    await callback.message.edit_text('Ща скину щащаща...')

    try:
        await callback.message.answer_video(
            video=FSInputFile(filename),
            caption='Лови видосик',
            request_timeout=120
        )
    except TelegramNetworkError:
        await callback.message.edit_text('Бот гавно, словил exceprion TelegramNetworkError(((')
        await callback.answer()
        
    os.remove(filename)
    await callback.message.delete()
    
