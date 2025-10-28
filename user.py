# handlers/user.py
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from config import ADMIN_ID


async def user_start(message: types.Message):
    """Команда /start для пользователя"""
    await message.answer(
        "Добро пожаловать! Вот доступные команды:\n"
        "/text - отправить текстовое сообщение\n"
        "/photo - отправить фото\n"
        "/help - помощь\n"
        "/about - описание бота"
    )


async def user_send_text(message: types.Message):
    """Пользователь отправляет текстовое сообщение"""
    user_info = f"Пользователь: {message.from_user.full_name} (ID: {message.from_user.id})"
    user_message = f"Сообщение: {message.text}"

    # Отправляем админу
    from main import bot
    await bot.send_message(
        ADMIN_ID,
        f"📨 Новое сообщение от пользователя:\n{user_info}\n{user_message}"
    )

    await message.answer("Ваше сообщение успешно отправлено!")


async def user_help(message: types.Message):
    """Команда помощи"""
    await message.answer(
        "Помощь по боту:\n"
        "- Используйте /text чтобы отправить сообщение\n"
        "- Используйте /photo чтобы отправить фото\n"
    )


async def user_about(message: types.Message):
    """Описание бота"""
    await message.answer(
        "Вы можете отправлять сообщения и фото."
    )


def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"])
    dp.register_message_handler(user_send_text, commands=["text"])
    dp.register_message_handler(user_help, commands=["help"])
    dp.register_message_handler(user_about, commands=["about"])

    # Обработчик обычных текстовых сообщений (не команд)
    dp.register_message_handler(user_send_text, content_types=types.ContentType.TEXT)