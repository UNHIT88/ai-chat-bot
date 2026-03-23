import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- Choreo အတွက် Flask Web Server (Health Check) ---
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Bot is running!", 200

def run_web_server():
    # Choreo က ပေးတဲ့ Port ကို ယူသုံးမယ်၊ မရှိရင် 8000 သုံးမယ်
    port = int(os.environ.get("PORT", 8000))
    web_app.run(host='0.0.0.0', port=port)
# --------------------------------------------------

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=API_KEY)
# မှတ်ချက်: gemini-2.5-flash မထွက်သေးပါက gemini-1.5-flash ဟု ပြောင်းသုံးနိုင်သည်
model = genai.GenerativeModel('gemini-2.5-flash')

def generate_content(full_prompt: str) -> str:
    try:
        response = model.generate_content(full_prompt)
        return response.text if hasattr(response, 'text') else "Sorry, I couldn't generate a response."
    except Exception as e:
        return f"Error: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"Hello {user_name}! I am a Gemini AI chatbot. How can I help you?")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    response_text = generate_content(user_message)
    await update.message.reply_text(response_text)

if __name__ == "__main__":
    # 1. Web Server ကို Background မှာ အရင် run ပါ
    threading.Thread(target=run_web_server, daemon=True).start()

    # 2. Telegram Bot ကို Build လုပ်ပါ
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("Bot is starting...")
    app.run_polling()
