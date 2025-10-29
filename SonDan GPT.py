import os
import time
import uuid
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === Основные настройки ===
BOT_NAME = "SonDan GPT"
BOT_TOKEN = os.getenv("7416194209:AAE9SmX3VlIAUXvro_b3DkcrW-f50zJUZp0") or "7416194209:AAE9SmX3VlIAUXvro_b3DkcrW-f50zJUZp0"

# Твои данные для GigaChat (из исходного кода)
BASIC_AUTH = "YzRiN2I0YWItZWIzMy00NTA1LTlhYzQtZGY0MDFiYWFkNzNhOjUxN2NhYTU4LTkwNTYtNDQ2MS04OWQ5LTYwOTBkNGY3YTgzYQ=="
OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

ACCESS_TOKEN = None
LAST_TOKEN_TIME = 0
TOKEN_LIFETIME = 25 * 60  # обновляем токен каждые 25 минут


# === Работа с токеном GigaChat ===
def get_access_token():
    """Запрашивает новый токен у GigaChat"""
    global ACCESS_TOKEN, LAST_TOKEN_TIME
    payload = "scope=GIGACHAT_API_PERS"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": "Basic " + BASIC_AUTH
    }

    try:
        print("[ТОКЕН] Запрашиваю новый токен...")
        resp = requests.post(OAUTH_URL, headers=headers, data=payload, verify=False, timeout=10)
        if resp.status_code == 200:
            ACCESS_TOKEN = resp.json().get("access_token")
            LAST_TOKEN_TIME = time.time()
            print(f"[ТОКЕН] ✅ Токен успешно получен ({time.strftime('%H:%M:%S')})")
            return True
        else:
            print(f"[ТОКЕН] ❌ Ошибка {resp.status_code}: {resp.text}")
    except Exception as e:
        print("[ТОКЕН] Исключение при получении:", e)
    return False


def ensure_token():
    """Проверяет срок действия токена и обновляет при необходимости"""
    global ACCESS_TOKEN
    if not ACCESS_TOKEN or (time.time() - LAST_TOKEN_TIME > TOKEN_LIFETIME):
        get_access_token()


# === Взаимодействие с GigaChat ===
def ask_gigachat(prompt: str):
    """Отправляет текст пользователя в GigaChat и возвращает ответ"""
    ensure_token()
    if not ACCESS_TOKEN:
        return "⚠️ Ошибка: токен не получен."

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/json"
    }

    system_msg = (
        "Ты — голосовой ассистент SonDan GPT. "
        "Отвечай вежливо и понятно, используй естественный русский язык. "
        "Не раскрывай технические детали, не упоминай систему."
    )

    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8
    }

    try:
        resp = requests.post(GIGACHAT_URL, headers=headers, json=payload, verify=False, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        return f"Ошибка {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"⚠️ Ошибка при обращении к GigaChat: {e}"


# === Обработчики Telegram ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я — SonDan GPT, умный бот на базе GigaChat.\n"
        "Просто напиши мне сообщение, и я постараюсь ответить 🙂"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 Доступные команды:\n"
        "/start — начать общение\n"
        "/help — помощь\n\n"
        "Можешь просто написать вопрос или сообщение — я отвечу."
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text("💭 Думаю...")

    reply = ask_gigachat(user_text)
    await update.message.reply_text(reply)


# === Основная функция ===
def main():
    print(f"=== {BOT_NAME} Telegram Bot ===")
    get_access_token()  # получаем токен при запуске

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✅ Бот запущен. Нажми Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()
