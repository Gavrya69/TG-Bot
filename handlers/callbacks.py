import os
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.exceptions import TelegramNetworkError

from services.downloader import select_format, download_video


router = Router()


@router.callback_query(F.data =='dl_no')
async def cancel_download(callback: CallbackQuery):
    
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith('dl_yes'))
async def start_download(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text('Checking video...')
    
    platform = callback.data.split(':')[1]
    url = callback.message.reply_to_message.text
    loop = asyncio.get_running_loop()
    
    if platform in ('yt', 'tt'):
        selected_format = await loop.run_in_executor(None, select_format, url, platform)
    else:
        print(f'[{__name__}] Unkown platform: {url}')
        await callback.message.edit_text('Unknown platform')
        return
    
    if selected_format is None:
        print(f'[{__name__}] Downloading is not possible: {url}')
        await callback.message.edit_text('Downloading is not possible')
        return
    
    file_size = (selected_format.get('filesize') or selected_format.get('filesize_approx'))/1024/1024
    file_resolution = selected_format.get('resolution')
    print(f'[{__name__}] Downloading file {file_size:.3} mb ({file_resolution}p): {url}')
    await callback.message.edit_text(f'Downloading...\n{file_size:.3} mb ({file_resolution}p)')

    filename = await loop.run_in_executor(None, download_video, url, selected_format, platform)

    
    if not filename:
        await callback.message.edit_text('Error')
        return
    
    print(f'[{__name__}] Sending file {file_size:.3} mb ({file_resolution}p): {filename}')
    await callback.message.edit_text('Sending...')


    try:
        with open(filename, 'rb') as f:
            await callback.message.answer_video(
                video=FSInputFile(filename),
                caption=f'Your video ({file_resolution})',
                request_timeout=180
            )
        print(f'[{__name__}] Successfully sended file {file_size:.3} mb ({file_resolution}p): {filename}')
        
    except TelegramNetworkError:
        print(f'[{__name__}] Failed to send video: {filename}')
        await callback.message.edit_text('Failed to send video')
        
    finally: 
        os.remove(filename)
        print(f'[{__name__}] Removed file: {filename}')
        await callback.message.delete()
    
