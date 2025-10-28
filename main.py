from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

from config import TOKEN_API, ADMIN_ID

bot = Bot(token=TOKEN_API)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Словарь для хранения пользователей и их состояний
users = {}
# ID последнего активного пользователя
last_user_id = None


class AdminStates(StatesGroup):
    waiting_for_message = State()


def get_user_reply_keyboard():
    """Обычная Reply-клавиатура для пользователя"""
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,  # Кнопки компактные
        one_time_keyboard=False  # Клавиатура не скрывается после использования
    )
    buttons = [
        types.KeyboardButton("📝 Отправить сообщение"),
        types.KeyboardButton("🖼️ Отправить фото"),
        types.KeyboardButton("📎 Отправить файл"),
        types.KeyboardButton("ℹ️ Помощь"),
    ]
    keyboard.add(*buttons)
    return keyboard


def get_admin_reply_keyboard():
    """Обычная Reply-клавиатура для администратора"""
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False
    )
    buttons = [
        types.KeyboardButton("📤 Ответить пользователю"),
        types.KeyboardButton("📋 Список пользователей")
    ]
    keyboard.add(*buttons)
    return keyboard


@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    user_id = message.from_user.id

    # Добавляем пользователя в словарь
    users[user_id] = {
        "name": message.from_user.full_name,
        "username": message.from_user.username
    }

    # Обновляем последнего активного пользователя
    global last_user_id
    last_user_id = user_id

    if user_id == ADMIN_ID:
        await message.answer(
            "👋 Вы администратор. Выберите действие:",
            reply_markup=get_admin_reply_keyboard()
        )
    else:
        await message.answer(
            "👋 Добро пожаловать!\n\n"
            "Выберите действие или просто отправьте мне сообщение/фото/файл:",
            reply_markup=get_user_reply_keyboard()
        )
        # Уведомляем администратора о новом пользователе
        await bot.send_message(
            ADMIN_ID,
            f"🆕 Новый пользователь написал боту:\n"
            f"Имя: {message.from_user.full_name}\n"
            f"ID: {user_id}\n"
            f"Username: @{message.from_user.username if message.from_user.username else 'нет'}"
        )


# Обработчики текстовых сообщений от обычных кнопок
@dp.message_handler(lambda message: message.text == "📝 Отправить сообщение")
async def process_text_message(message: types.Message):
    await message.answer("📝 Напишите ваше сообщение:")


@dp.message_handler(lambda message: message.text == "🖼️ Отправить фото")
async def process_photo_message(message: types.Message):
    await message.answer("🖼️ Отправьте фото:")


@dp.message_handler(lambda message: message.text == "📎 Отправить файл")
async def process_file_message(message: types.Message):
    await message.answer("📎 Отправьте файл:")


@dp.message_handler(lambda message: message.text == "ℹ️ Помощь")
async def process_help_message(message: types.Message):
    await message.answer(
        "ℹ️ Помощь по боту:\n\n"
        "• Вы можете отправлять текстовые сообщения, фото и файлы\n"
        "• Для быстрого доступа к функциям используйте кнопки меню"
    )


@dp.message_handler(lambda message: message.text == "📤 Ответить пользователю")
async def process_admin_send(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав администратора")
        return

    global last_user_id

    if not users or last_user_id is None:
        await message.answer("❌ Пока нет пользователей, которые написали боту")
        return

    await message.answer(
        f"✍️ Введите сообщение для отправки пользователю.\n"
        f"Получатель: {users[last_user_id]['name']} (ID: {last_user_id})"
    )
    await AdminStates.waiting_for_message.set()


@dp.message_handler(lambda message: message.text == "📋 Список пользователей")
async def process_admin_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав для просмотра списка пользователей")
        return

    if not users:
        await message.answer("📝 Пользователей пока нет")
        return

    users_list = "📋 Список пользователей:\n\n"
    for uid, user_data in users.items():
        users_list += f"• {user_data['name']} (ID: {uid})"
        if user_data.get('username'):
            users_list += f" @{user_data['username']}"
        users_list += "\n"

    await message.answer(users_list)


@dp.message_handler(commands=["myid"])
async def get_my_id(message: types.Message):
    await message.answer(f"🆔 Ваш ID: `{message.from_user.id}`", parse_mode="Markdown")


@dp.message_handler(commands=["users"])
async def list_users(message: types.Message):
    """Показать список пользователей (только для админа)"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав для просмотра списка пользователей")
        return

    if not users:
        await message.answer("📝 Пользователей пока нет")
        return

    users_list = "📋 Список пользователей:\n\n"
    for uid, user_data in users.items():
        users_list += f"• {user_data['name']} (ID: {uid})"
        if user_data.get('username'):
            users_list += f" @{user_data['username']}"
        users_list += "\n"

    await message.answer(users_list)


@dp.message_handler(commands=["send"])
async def admin_send_message(message: types.Message):
    """Команда для отправки сообщения пользователю"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав администратора")
        return

    global last_user_id

    if not users or last_user_id is None:
        await message.answer("❌ Пока нет пользователей, которые написали боту")
        return

    await message.answer(
        f"✍️ Введите сообщение для отправки пользователю.\n"
        f"Получатель: {users[last_user_id]['name']} (ID: {last_user_id})"
    )
    await AdminStates.waiting_for_message.set()


@dp.message_handler(state=AdminStates.waiting_for_message)
async def process_admin_message(message: types.Message, state: FSMContext):
    """Обработка сообщения от администратора"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав администратора")
        await state.finish()
        return

    global last_user_id

    try:
        # Отправляем сообщение пользователю
        await bot.send_message(
            last_user_id,
            f"📩 Сообщение от администратора:\n\n{message.text}"
        )
        await message.answer("✅ Сообщение отправлено пользователю!")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}")

    await state.finish()


@dp.message_handler(content_types=[types.ContentType.TEXT])
async def handle_user_messages(message: types.Message):
    """Обработка текстовых сообщений от пользователей"""
    user_id = message.from_user.id

    # Игнорируем команды и кнопки (они обрабатываются отдельно)
    if message.text.startswith('/') or message.text in [
        "📝 Отправить сообщение", "🖼️ Отправить фото", "📎 Отправить файл",
        "ℹ️ Помощь", "📤 Ответить пользователю", "📋 Список пользователей"
    ]:
        return

    # Если это админ, не обрабатываем как пользовательское сообщение
    if user_id == ADMIN_ID:
        return

    # Добавляем/обновляем пользователя
    users[user_id] = {
        "name": message.from_user.full_name,
        "username": message.from_user.username
    }

    # Обновляем последнего активного пользователя
    global last_user_id
    last_user_id = user_id

    user_info = f"Пользователь: {message.from_user.full_name} (ID: {user_id})"

    # Отправляем сообщение админу
    await bot.send_message(
        ADMIN_ID,
        f"📨 Сообщение от пользователя:\n{user_info}\n\nТекст: {message.text}"
    )

    await message.answer("✅ Ваше сообщение успешно отправлено!", reply_markup=get_user_reply_keyboard())


@dp.message_handler(content_types=[types.ContentType.PHOTO])
async def handle_user_photos(message: types.Message):
    """Обработка фото от пользователей"""
    user_id = message.from_user.id

    # Если это админ, не обрабатываем
    if user_id == ADMIN_ID:
        return

    # Добавляем/обновляем пользователя
    users[user_id] = {
        "name": message.from_user.full_name,
        "username": message.from_user.username
    }

    # Обновляем последнего активного пользователя
    global last_user_id
    last_user_id = user_id

    user_info = f"Пользователь: {message.from_user.full_name} (ID: {user_id})"

    # Отправляем фото админу
    caption = message.caption or ""
    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"📸 Фото от пользователя:\n{user_info}\n\nПодпись: {caption}"
    )

    await message.answer("✅ Ваше фото успешно отправлено!", reply_markup=get_user_reply_keyboard())


@dp.message_handler(content_types=[types.ContentType.DOCUMENT])
async def handle_user_documents(message: types.Message):
    """Обработка файлов от пользователей"""
    user_id = message.from_user.id

    # Если это админ, не обрабатываем
    if user_id == ADMIN_ID:
        return

    # Добавляем/обновляем пользователя
    users[user_id] = {
        "name": message.from_user.full_name,
        "username": message.from_user.username
    }

    # Обновляем последнего активного пользователя
    global last_user_id
    last_user_id = user_id

    user_info = f"Пользователь: {message.from_user.full_name} (ID: {user_id})"

    # Отправляем файл админу
    caption = message.caption or ""
    await bot.send_document(
        ADMIN_ID,
        message.document.file_id,
        caption=f"📎 Файл от пользователя:\n{user_info}\n\nОписание: {caption}"
    )

    await message.answer("✅ Ваш файл успешно отправлен", reply_markup=get_user_reply_keyboard())


@dp.message_handler(content_types=[types.ContentType.VIDEO, types.ContentType.AUDIO, types.ContentType.VOICE])
async def handle_user_media(message: types.Message):
    """Обработка видео, аудио и голосовых сообщений от пользователей"""
    user_id = message.from_user.id

    # Если это админ, не обрабатываем
    if user_id == ADMIN_ID:
        return

    # Добавляем/обновляем пользователя
    users[user_id] = {
        "name": message.from_user.full_name,
        "username": message.from_user.username
    }

    # Обновляем последнего активного пользователя
    global last_user_id
    last_user_id = user_id

    user_info = f"Пользователь: {message.from_user.full_name} (ID: {user_id})"

    # Определяем тип медиа и отправляем админу
    media_type = ""
    if message.content_type == types.ContentType.VIDEO:
        media_type = "🎥 Видео"
        await bot.send_video(ADMIN_ID, message.video.file_id, caption=f"{media_type} от пользователя:\n{user_info}")
    elif message.content_type == types.ContentType.AUDIO:
        media_type = "🎵 Аудио"
        await bot.send_audio(ADMIN_ID, message.audio.file_id, caption=f"{media_type} от пользователя:\n{user_info}")
    elif message.content_type == types.ContentType.VOICE:
        media_type = "🎤 Голосовое сообщение"
        await bot.send_voice(ADMIN_ID, message.voice.file_id, caption=f"{media_type} от пользователя:\n{user_info}")

    await message.answer(f"✅ Ваше {media_type.lower()} успешно отправлено!", reply_markup=get_user_reply_keyboard())


if __name__ == "__main__":
    print("Бот запущен...")
    executor.start_polling(dp, skip_updates=True)