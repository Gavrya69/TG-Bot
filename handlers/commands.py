from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('start')


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('help')


@router.message(Command('i_love_you'))
async def cmd_help(message: Message):
    await message.reply('иди нахуй)))0)')
