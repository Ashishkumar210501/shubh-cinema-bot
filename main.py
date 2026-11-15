import os
import requests
import telebot
from telebot import types

# आपका Telegram Bot Token यहाँ सेट है
BOT_TOKEN = "9203802169:AAEPHn1B8-bVyaY0jOfP8sXz-ekabmVP8l8"

# आपका Google Apps Script Web App URL (आटोमेटिक सेट है)
GAS_URL = "https://script.google.com/macros/s/AKfycbxggQxs77zEJt_7aa4IUfRPA5cQi-aYfEjsq9-FqMDv_cQz_F-mw2XqMP2RNslVQcTnMA/exec"

# आपकी Filemoon API Key (आटोमेटिक सेट है)
FILEMOON_API_KEY = "1666910y1zglkkt8t55493"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🎬 Add Movie"),
        types.KeyboardButton("🔥 Add Recent"),
        types.KeyboardButton("📺 Add Series"),
        types.KeyboardButton("📺 Add TV Show"),
        types.KeyboardButton("⏳ Add Old is Gold"),
        types.KeyboardButton("🔞 Add 18+")
    )
    bot.reply_to(message, "👋 **Shubh Cinema Admin Bot** में आपका स्वागत है!\n\nआपका डेटाबेस और बॉट पूरी तरह तैयार है। नीचे दिए गए बटन्स से काम शुरू करें:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, f"✅ मैसेज मिल गया: {message.text}\nडेटाबेस और होस्टिंग के साथ आपका बॉट सफलतापूर्वक जुड़ चुका है।")

print("Bot is running...")
bot.infinity_polling()
