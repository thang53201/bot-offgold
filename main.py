import os
import time
from dotenv import load_dotenv
from telegram import Bot
from monitor import build_alerts

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("Thiếu BOT_TOKEN hoặc CHAT_ID")

bot = Bot(TOKEN)

last = {"y10": None, "spdr_tons": None}

bot.send_message(chat_id=CHAT_ID, text="🚀 Bot Gold Alert khởi động (FULL).")

while True:
    alerts, last = build_alerts(last)
    if alerts:
        now = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
        header = f"⚠️ *GOLD ALERT* — {now}\n"
        body = "\n".join(f"- {a}" for a in alerts)
        footer = "\n\n→ *Rủi ro:* Vàng có thể chạy mạnh 1000–1500 pips. Xem xét giảm DCA hoặc hedge."
        msg = header + body + footer
        bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

    time.sleep(60)
