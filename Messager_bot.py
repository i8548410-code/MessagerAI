import io, json, os, base64, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# 🔐 Tokenlarni bu yerga yozing
OPENAI_API_KEY = "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"
TELEGRAM_TOKEN = "8289814701:AAHny6yjD2nAky_XfXy5gM9CW3Df9f6tNKc"

client = OpenAI(api_key=OPENAI_API_KEY)
CHAT_HISTORY_FILE = "chat_history.json"

# 🔄 Suhbat tarixini fayl orqali yuklash/saqlash
def load_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(data):
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

chat_history = load_history()

# 🔹 /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    chat_history[user_id] = []
    save_history(chat_history)
    await update.message.reply_text(
        "👋 Salom! Men AI botman.\n"
        "Menga yozing — men siz bilan o‘zbek, rus yoki ingliz tilida suhbatlashaman.\n"
        "Shuningdek, rasm yuborsangiz, uni tahlil qilaman 📸."
    )

# 💬 Matnli chat
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_message = update.message.text

    if user_id not in chat_history:
        chat_history[user_id] = []

    chat_history[user_id].append({"role": "user", "content": user_message})
    chat_history[user_id] = chat_history[user_id][-5:]  # faqat oxirgi 5 ta xabarni saqlaymiz

    try:
        response = await asyncio.to_thread(lambda: client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Siz foydalanuvchi bilan o‘zbek, rus yoki ingliz tilida samimiy va foydali tarzda suhbatlashadigan sun’iy intellektsiz."}
            ] + chat_history[user_id],
        ))
        bot_reply = response.choices[0].message.content
    except Exception as e:
        bot_reply = f"⚠️ Xato: {e}"

    chat_history[user_id].append({"role": "assistant", "content": bot_reply})
    save_history(chat_history)
    await update.message.reply_text(bot_reply)

# 🖼️ Rasmni tahlil qilish
async def analyze_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_bytes = await file.download_as_bytearray()
    image_base64 = base64.b64encode(file_bytes).decode("utf-8")

    try:
        response = await asyncio.to_thread(lambda: client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Siz foydalanuvchining yuborgan rasmini tahlil qiluvchi AI yordamchisiz."},
                {"role": "user", "content": [
                    {"type": "text", "text": "Bu rasmda nima bor?"},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_base64}"}
                ]}
            ]
        ))
        description = response.choices[0].message.content
    except Exception as e:
        description = f"⚠️ Rasmni tahlil qilishda xato: {e}"

    await update.message.reply_text(description)

# 🚀 Botni ishga tushurish
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analyze_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("🤖 Tez ishlaydigan AI Telegram bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
