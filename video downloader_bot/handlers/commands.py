import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from services.cookies import reason_to_user_message, save_cookies

router = Router()
logger = logging.getLogger(__name__)


class CookiesStates(StatesGroup):
    waiting_file = State()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer("...")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer("<:")


@router.message(Command("load_cookies"))
async def cmd_load_cookies(message: Message, state: FSMContext) -> None:
    if message.chat.type != "private":
        await message.answer("Эту команду можно использовать только в личных сообщениях с ботом.")
        return

    await state.set_state(CookiesStates.waiting_file)
    await message.answer(
        "Пришли файл cookies.txt (Netscape HTTP Cookie File) как документ.\n"
        "Отмена: /cancel"
    )


@router.message(Command("cancel"), StateFilter(CookiesStates.waiting_file))
async def cmd_cancel_cookies(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Загрузка cookies отменена.")


@router.message(CookiesStates.waiting_file, F.document)
async def receive_cookies_document(message: Message, state: FSMContext) -> None:
    document = message.document
    if document is None:
        await message.answer("Нужен файл-документ. Попробуй ещё раз или /cancel")
        return

    # Soft size limit (cookies files are small)
    if document.file_size and document.file_size > 512 * 1024:
        await message.answer("Файл слишком большой (лимит 512 KB).")
        return

    try:
        buffer = await message.bot.download(document)
        if buffer is None:
            await message.answer("Не удалось скачать файл из Telegram. Попробуй ещё раз.")
            return
        content = buffer.read()
    except Exception:
        logger.exception("Failed to download cookies document from Telegram")
        await message.answer("Не удалось скачать файл из Telegram. Попробуй ещё раз.")
        return

    ok, reason = save_cookies(content)
    if not ok:
        await message.answer(
            f"Не удалось сохранить cookies.\n{reason_to_user_message(reason)}\n\n"
            "Пришли другой файл или /cancel"
        )
        return

    await state.clear()
    await message.answer(f"Cookies сохранены.\n{reason_to_user_message(reason)}")
    user_id = message.from_user.id if message.from_user else "?"
    logger.info("User %s updated cookies (%s)", user_id, reason)


@router.message(CookiesStates.waiting_file)
async def receive_cookies_wrong_type(message: Message) -> None:
    await message.answer(
        "Нужен именно файл-документ (cookies.txt).\n"
        "Пришли документ или /cancel"
    )
