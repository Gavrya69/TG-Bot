from typing import Final
import asyncio
import re
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from core import download_youtube

from dotenv import load_dotenv
load_dotenv()

TOKEN: Final = os.getenv('TOKEN')
BOT_USERNAME: Final = '@Muhins_son_bot'
URL_RE = re.compile(r"https?://\S+")

#===================================================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('reply')
    
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('help')
    
async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('custom')
    
#===================================================================================================

# Responses
def handle_response(text: str) -> str:
    processed: str = text.lower()
    
    return '?'
    
    
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
    response: str = handle_response(text)
    
    print(text)
    
    url = URL_RE.findall(text)[0] if URL_RE.findall(text) else False
    if not url: return
    
    await update.message.reply_text('Ща погодь...')
    loop = asyncio.get_running_loop()
    video_path, w, h = await loop.run_in_executor(None, download_youtube, url)
    
    if not video_path: 
        await update.message.reply_text('Нихуя не вышло((9(')
        return
    
    await update.message.reply_text('Ща-ща-ща, почти...')
    
    await update.message.reply_video(
        video=open(video_path, 'rb'),
        caption=f'Заебок))0), лови в {w}x{h}'
    )
    
    os.remove(video_path)
    
    
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #print(f'Update {update} caused error {context.error}')
    pass
    
    
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass



#===================================================================================================

def main():
    print('Starting...')
    
    app = Application.builder().token(TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    # Errors
    app.add_error_handler(error)
    
    print('Polling...')
    app.run_polling(poll_interval=1)
    
if __name__ == '__main__':
    main()
    
