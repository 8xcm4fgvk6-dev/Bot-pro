import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json, os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

# ---------- DATA ----------
def load():
    with open("data.json", "r") as f:
        return json.load(f)

def save(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)

data = load()

# ---------- TEXTS ----------
TEXT = {
    "uz": {
        "start": "🎬 Video botga xush kelibsiz!",
        "menu": "Asosiy menyu",
        "sub": "📢 Avval barcha kanallarga obuna bo‘ling",
        "ok": "✅ Obuna bo‘ldim",
        "code": "🎥 Kod kiritish",
        "private": "🔒 Private kontent",
        "denied": "❌ Sizda ruxsat yo‘q"
    },
    "ru": {
        "start": "🎬 Добро пожаловать в видео бот!",
        "menu": "Главное меню",
        "sub": "📢 Подпишитесь на все каналы",
        "ok": "✅ Я подписался",
        "code": "🎥 Ввести код",
        "private": "🔒 Приватный контент",
        "denied": "❌ У вас нет доступа"
    }
}

# ---------- HELPERS ----------
def subscribed(user_id):
    for ch in data["channels"]:
        try:
            if bot.get_chat_member(ch, user_id).status == "left":
                return False
        except:
            return False
    return True

def menu(lang):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(TEXT[lang]["code"], callback_data="code"),
        InlineKeyboardButton(TEXT[lang]["private"], callback_data="private")
    )
    return kb

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(m):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🇺🇿 O‘zbek", callback_data="lang_uz"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
    )
    bot.send_message(m.chat.id, "🌍 Tilni tanlang / Выберите язык", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
def set_lang(c):
    lang = c.data.split("_")[1]
    data["users"][str(c.from_user.id)] = {"lang": lang}
    save(data)
    bot.send_message(c.message.chat.id, TEXT[lang]["start"], reply_markup=menu(lang))

# ---------- USER ----------
@bot.callback_query_handler(func=lambda c: c.data == "code")
def ask_code(c):
    uid = str(c.from_user.id)
    lang = data["users"][uid]["lang"]
    if not subscribed(c.from_user.id):
        bot.send_message(c.message.chat.id, TEXT[lang]["sub"])
        return
    bot.send_message(c.message.chat.id, "🔑 Kodni yuboring")

@bot.message_handler(func=lambda m: m.text and m.text in data["codes"])
def send_video(m):
    code = m.text
    video_id = data["codes"][code]
    bot.send_video(m.chat.id, video_id)

@bot.callback_query_handler(func=lambda c: c.data == "private")
def private(c):
    uid = c.from_user.id
    lang = data["users"][str(uid)]["lang"]
    if uid not in data["private_users"]:
        bot.send_message(c.message.chat.id, TEXT[lang]["denied"])
    else:
        bot.send_message(c.message.chat.id, "🔓 Private kontent ochildi")

# ---------- ADMIN PANEL ----------
@bot.message_handler(commands=["admin"])
def admin(m):
    if m.from_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("➕ Kod qo‘shish", callback_data="add_code"),
        InlineKeyboardButton("🔒 Private user", callback_data="add_private")
    )
    bot.send_message(m.chat.id, "👑 Admin panel", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "add_code")
def add_code(c):
    if c.from_user.id != ADMIN_ID:
        return
    bot.send_message(c.message.chat.id, "Format:\nKOD + video yubor")

@bot.message_handler(content_types=["video"])
def admin_video(m):
    if m.from_user.id != ADMIN_ID:
        return
    code = m.caption
    if not code:
        return
    data["codes"][code] = m.video.file_id
    save(data)
    bot.send_message(m.chat.id, f"✅ Kod qo‘shildi: {code}")

bot.infinity_polling()
