import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

bot = Bot(token='123')
dp= Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('start')


@dp.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('help')



async def main():
    await dp.start_polling(bot)
    
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f'[{__name__}] Exit.')

























# import asyncio
# import re
# import os
# from dotenv import load_dotenv

# from telegram import Update
# from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# from telegram import InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import CallbackQueryHandler

# from core import download_youtube

# load_dotenv()
# TOKEN: str = os.getenv('TOKEN')
# BOT_USERNAME: str = os.getenv('BOT_USERNAME')

# URL_RE = re.compile(r"https?://\S+")

# #===================================================================================================

# async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text('start')
    
# async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text('help')
    
# async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text('custom')
    
# #===================================================================================================

    
# async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     text: str = update.message.text
    
#     url = URL_RE.findall(text)[0] if URL_RE.findall(text) else False
#     if not url: return
#     buttons = InlineKeyboardMarkup([
#         [
#             InlineKeyboardButton('Да', callback_data=url),
#             InlineKeyboardButton('Нет', callback_data=None),
#         ]
#     ])
    
#     await update.message.reply_text(
#         'Скачать?',
#         reply_markup=buttons,
#     )


# async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()

#     url = query.data

#     if not url :
#         await query.edit_message_text('Мне в падлу скачивать')
#         return

#     await query.edit_message_text('Ша погодь...')

#     loop = asyncio.get_running_loop()
#     video_path, w, h = await loop.run_in_executor(None, download_youtube, url)

#     if not video_path:
#         await query.message.reply_text('Бля, не вышло(((')
#         return

#     await query.message.reply_video(
#         video=open(video_path, 'rb'),
#         caption=f'Заебок))0), лови в {w}x{h}'
#     )

#     os.remove(video_path)

    
# async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     #print(f'Update {update} caused error {context.error}')
#     pass
    
    
# async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     pass



# #===================================================================================================

# def main():
#     print(f'[{__name__}] Starting...')
    
#     app = Application.builder().token(TOKEN).build()
    
#     # Commands
#     app.add_handler(CommandHandler('start', start_command))
#     app.add_handler(CommandHandler('help', help_command))
#     app.add_handler(CommandHandler('custom', custom_command))

#     # Messages
#     app.add_handler(MessageHandler(filters.TEXT, handle_message))
#     app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
#     # Errors
#     app.add_error_handler(error)
    
#     print(f'[{__name__}] Polling...')
#     app.run_polling(poll_interval=1)
    
# if __name__ == '__main__':
#     main()
    
