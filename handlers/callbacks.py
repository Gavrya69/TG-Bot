from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.downloader import download_youtube

router = Router()

@router.callback_query(F.data == 'cancel')
async def cancel_download(callback: CallbackQuery):
    await callback.message.edit_text('похуй, не хочу скачивать')
    await callback.answer()


@router.callback_query(F.data.startswith('download:'))
async def start_download(callback: CallbackQuery):
    await callback.answer('Ща скачаю погодь...')

    url = callback.data.split("download:", 1)[1]
