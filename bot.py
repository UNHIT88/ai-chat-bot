import os
import threading
import openai
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

# --- Choreo Health Check (Port 8000) ---
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Bot is running with AICC Key!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 8000))
    web_app.run(host='0.0.0.0', port=port)

# --- AICC API Configuration ---
# Choreo ရဲ့ Environment Variable ထဲမှာ GEMINI_API_KEY ဆိုတဲ့နာမည်နဲ့ sk-... key ကို ထည့်ပေးပါ
client = openai.OpenAI(
    api_key=os.environ.get("GEMINI_API_KEY"),
    base_url="https://api.aicc.io/v1" # AICC ရဲ့ endpoint ဖြစ်ရပါမယ်
)

def generate_content(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gemini-1.5-flash", # AICC မှာ ပေးထားတဲ့ model name အတိုင်း သုံးပါ
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# --- Telegram Bot Logic ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Hello {update.effective_user.first_name}! Bot is online using AICC.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    # Typing... ပြပေးရန်
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    response_text = generate_content(user_message)
    await update.message.reply_text(response_text)

if __name__ == "__main__":
    # 1. Start Flask in background
    threading.Thread(target=run_web_server, daemon=True).start()

    # 2. Start Telegram Bot
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("Bot is starting...")
    app.run_polling()
