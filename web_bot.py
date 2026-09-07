import os
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

TOKEN = "ТВОЙ_НОВЫЙ_ТОКЕН"
GROUP_ID = -1003218790551
PUBLIC_CHAT_ID = -1003503911588

# Твоя публичная ссылка с Render (без слэша на конце!)
WEBHOOK_URL = "https://icepro-bot-1.onrender.com"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
BASE_WEBHOOK_URL = f"{WEBHOOK_URL}{WEBHOOK_PATH}"

PORT = int(os.environ.get("PORT", 8080))

dp = Dispatcher()
bot = Bot(token=TOKEN)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я официальный бот Совета ICEPRO.\n"
        "Напиши свой вопрос или предложение здесь, "
        "и я передам его Совету команды."
    )

@dp.message(Command("post"))
async def post_to_public(message: Message):
    if message.chat.id != GROUP_ID:
        await message.reply("⚠️ Эту команду можно использовать только в чате Совета!")
        return

    command_text = message.text
    if len(command_text) <= 5:
        await message.reply("⚠️ Вы не написали текст решения. Пример:\n/post Внимание, тренировка переносится")
        return

    post_content = command_text[5:].strip()
    official_announcement = (
        "📢 ОФИЦИАЛЬНОЕ РЕШЕНИЕ СОВЕТА ICEPRO 📢\n\n"
        f"{post_content}"
    )

    try:
        await bot.send_message(PUBLIC_CHAT_ID, official_announcement)
        await message.react([{"type": "emoji", "emoji": "🔥"}])
    except Exception as e:
        await message.reply(f"❌ Ошибка публикации: {e}")

@dp.message(F.chat.type == "private")
async def forward_to_group(message: Message):
    if message.text and message.text.startswith('/'):
        return

    user = message.from_user
    username = f"@{user.username}" if user.username else "без юзернейма"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

    text_for_council = (
        "📩 Новый вопрос от игрока!\n"
        f"👤 От: {full_name} ({username})\n"
        f"🆔 ID игрока: {user.id}\n\n"
        f"💬 Текст:\n{message.text}"
    )

    await bot.send_message(GROUP_ID, text_for_council)
    await message.answer("✅ Твой вопрос отправлен Совету ICEPRO. Скоро вернемся с ответом!")

@dp.message(F.chat.id == GROUP_ID)
async def reply_from_council(message: Message):
    if message.text and message.text.startswith('/'):
        return

    if message.reply_to_message:
        replied_text = message.reply_to_message.text
        if "🆔 ID игрока:" in replied_text:
            try:
                lines = replied_text.split('\n')
                for line in lines:
                    if "🆔 ID игрока:" in line:
                        target_id = int(line.replace("🆔 ID игрока:", "").strip())
                        await bot.send_message(
                            target_id, 
                            f"📢 Ответ от Совета ICEPRO:\n\n{message.text}"
                        )
                        await message.react([{"type": "emoji", "emoji": "👍"}])
                        break
            except Exception as e:
                print(f"Ошибка при отправке ответа: {e}")

async def on_startup(bot: Bot):
    # Устанавливаем вебхук при запуске
    await bot.set_webhook(BASE_WEBHOOK_URL)

def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    app = web.Application()
    
    # Регистрируем обработчик вебхука от aiogram
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Настраиваем приложение
    setup_application(app, dp, bot=bot)
    app.on_startup.append(lambda app: on_startup(bot))
    
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
