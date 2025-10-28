# handlers/admin.py
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import ADMIN_ID


class AdminStates(StatesGroup):
    waiting_for_message = State()


# Глобальная переменная для user_id (будет устанавливаться из main.py)
user_id = None


async def admin_send_message(message: types.Message):
    """Команда для отправки сообщения пользователю"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав администратора")
        return

    if not user_id:
        await message.answer("❌ Пользователь еще не написал боту")
        return

    await message.answer("✍️ Введите сообщение для отправки пользователю:")
    await AdminStates.waiting_for_message.set()


async def process_admin_message(message: types.Message, state: FSMContext, bot):
    """Обработка сообщения от администратора"""
    global user_id

    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав администратора")
        await state.finish()
        return

    if not user_id:
        await message.answer("❌ Пользователь еще не написал боту")
        await state.finish()
        return

    try:
        # Отправляем сообщение пользователю
        await bot.send_message(user_id, f"📩 Сообщение от администратора:\n\n{message.text}")
        await message.answer("✅ Сообщение отправлено пользователю!")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}")

    await state.finish()


def register_admin_handlers(dp: Dispatcher, bot_instance):
    """Регистрация обработчиков с передачей бота"""
    # Используем lambda для передачи bot в обработчик
    dp.register_message_handler(
        lambda message: process_admin_message(message, None, bot_instance),
        state=AdminStates.waiting_for_message
    )
    dp.register_message_handler(admin_send_message, commands=["send"], state="*")