import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

TOKEN = "8829675416:AAGqYBN2XTLGeL-ImYBqXT1Cra5aiskXPQA"

# ID чата Совета (куда прилетают вопросы от игроков)
GROUP_ID = -1003218790551

# ID Общего чата команды (куда бот публикует официальные решения)
PUBLIC_CHAT_ID = -1003503911588

dp = Dispatcher()

# 1. Приветствие для игроков в ЛС
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я официальный бот Совета ICEPRO.\n"
        "Напиши свой вопрос или предложение здесь, "
        "и я передам его Совету команды."
    )

# 2. Функция публикации решений в общий чат через команду /post
# Писать в чате Совета так: /post Текст важного решения
@dp.message(Command("post"))
async def post_to_public(message: Message, bot: Bot):
    # Проверяем, что команду написали именно в чате Совета
    if message.chat.id != GROUP_ID:
        await message.reply("⚠️ Эту команду можно использовать только в чате Совета!")
        return

    # Убираем слово /post из текста
    command_text = message.text
    if len(command_text) <= 5:
        await message.reply("⚠️ Вы не написали текст решения. Пример:\n`/post Внимание, тренировка переносится`", parse_mode="Markdown")
        return

    post_content = command_text[5:].strip() # Отрезаем '/post '

    # Красиво оформляем официальное сообщение от Совета
    official_announcement = (
        f"📢 **ОФИЦИАЛЬНОЕ РЕШЕНИЕ СОВЕТА ICEPRO** 📢\n\n"
        f"{post_content}"
    )

    try:
        # Отправляем в Общий чат команды от лица бота
        await bot.send_message(PUBLIC_CHAT_ID, official_announcement, parse_mode="Markdown")
        # Ставим галочку/огонек в чате Совета в знак успеха
        await message.react([{"type": "emoji", "emoji": "🔥"}])
    except Exception as e:
        await message.reply(f"❌ Ошибка публикации (убедись, что бот админ в общем чате): {e}")

# 3. Обработка сообщений в ЛС (пересылка вопросов в чат Совета)
@dp.message(F.chat.type == "private")
async def forward_to_group(message: Message, bot: Bot):
    if message.text and message.text.startswith('/'):
        return

    user = message.from_user
    username = f"@{user.username}" if user.username else "без юзернейма"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

    text_for_council = (
        f"📩 **Вопрос от игрока!**\n"
        f"👤 От: {full_name} ({username})\n"
        f"🆔 ID игрока: `{user.id}`\n\n"
        f"💬 Текст:\n{message.text}"
    )

    await bot.send_message(GROUP_ID, text_for_council, parse_mode="Markdown")
    await message.answer("✅ Твой вопрос отправлен Совету ICEPRO. Скоро вернемся с ответом!")

# 4. Ответ из чата Совета обратно игроку (через Reply)
@dp.message(F.chat.id == GROUP_ID)
async def reply_from_council(message: Message, bot: Bot):
    # Игнорируем команду /post в этом обработчике
    if message.text and message.text.startswith('/'):
        return

    if message.reply_to_message:
        replied_text = message.reply_to_message.text
        
        if "🆔 ID игрока:" in replied_text:
            try:
                lines = replied_text.split('\n')
                for line in lines:
                    if "🆔 ID игрока:" in line:
                        target_id = int(line.replace("🆔 ID игрока:", "").replace("`", "").strip())
                        
                        await bot.send_message(
                            target_id, 
                            f"📢 **Ответ от Совета ICEPRO:**\n\n{message.text}"
                        )
                        await message.react([{"type": "emoji", "emoji": "👍"}])
                        break
            except Exception as e:
                print(f"Ошибка при отправке ответа: {e}")

async def main():
    bot = Bot(token=TOKEN)
    print("Бот обновлен и полностью готов к работе!")
    await dp.start_polling(bot)   

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
