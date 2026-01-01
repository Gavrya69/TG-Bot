import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from services.downloader import download_youtube

router = Router()

@router.callback_query(F.data =='dl_no')
async def cancel_download(callback: CallbackQuery):
    
    await callback.message.edit_text('похуй, не хочу скачивать')
    await callback.answer()

@router.callback_query(F.data =='dl_yes')
async def start_download(callback: CallbackQuery):
    user_msg = callback.message.reply_to_message
    msg = await callback.message.edit_text('Ща скачаю погодь...')
    
    filename = download_youtube(callback.message.reply_to_message.text)
    
    if not filename:
        await callback.message.edit_text('Чот не вышло нихуя(')
        await callback.answer()
        return
    
    await callback.message.edit_text('Ща скину щащаща...')
    
    await user_msg.reply_video(
        video=FSInputFile(filename),
        caption='Лови видосик'
    )
    
    os.remove(filename)
    await msg.delete()
    await callback.answer()
    
