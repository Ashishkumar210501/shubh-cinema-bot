import os
import requests
import telebot
from telebot import types
import threading
import time

# आपका Telegram Bot Token यहाँ सेट है
BOT_TOKEN = "9203802169:AAEPHn1B8-bVyaY0jOfP8sXz-ekabmVP8l8"

# आपका नया Google Apps Script Web App URL
GAS_URL = "https://script.google.com/macros/s/AKfycbztwsN4aJUJXzzkuyK7Ra8CtsbbUnHkISwOhfeUrNC2VNhgyd1mzd6eOWaJT8nZNb2IpA/exec"

bot = telebot.TeleBot(BOT_TOKEN)

# अस्थाई रूप से यूजर का डेटा स्टोर करने के लिए डिक्शनरी
user_pending_data = {}

# 1. /start कमांड और कीबोर्ड बटन्स
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🎬 Add Movie"),
        types.KeyboardButton("🔥 Add Recent"),
        types.KeyboardButton("📺 Add Series"),
        types.KeyboardButton("📺 Add TV Show"),
        types.KeyboardButton("⏳ Old Is Gold"),
        types.KeyboardButton("🔞 Adult")
    )
    bot.reply_to(
        message,
        "👋 **Shubh Cinema Admin Bot में आपका स्वागत है!**\n\n"
        "🎬 अपने प्राइवेट चैनल से वीडियो को सीधे इस बॉट पर **Forward** करें।\n"
        "बॉट उसका असली नाम डिटेक्ट करके सही डिटेल्स के साथ Google Sheet में जोड़ देगा।",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# 2. Google Sheet में डेटा भेजने का फंक्शन
def save_to_google_sheet(sheet_name, data_dict):
    payload = {
        "sheetName": sheet_name,
        "data": data_dict
    }
    try:
        response = requests.post(GAS_URL, json=payload)
        return response.json()
    except Exception as e:
        print(f"Sheet Error: {e}")
        return {"status": "error"}

# 3. जब एडमिन वीडियो फॉरवर्ड करे या लिंक भेजे
@bot.message_handler(content_types=['text', 'video', 'document', 'audio'])
def handle_incoming_content(message):
    if message.text in ["🎬 Add Movie", "🔥 Add Recent", "📺 Add Series", "📺 Add TV Show", "⏳ Old Is Gold", "🔞 Adult"]:
        bot.reply_to(message, "📌 कृपया इस टैब में जोड़ने के लिए अपने प्राइवेट चैनल से वीडियो **यहाँ Forward करें**:")
        return

    video_link = None
    detected_title = "Uploaded Video"
    
    # अगर यूजर ने प्राइवेट चैनल से वीडियो सीधे बॉट को Forward किया है
    if message.video or message.document or message.audio:
        file_obj = message.video or message.document or message.audio
        file_id = file_obj.file_id
        
        # फाइल का असली नाम (FileName) निकालने की कोशिश
        if hasattr(file_obj, 'file_name') and file_obj.file_name:
            detected_title = file_obj.file_name.rsplit('.', 1)[0].replace('_', ' ').replace('.', ' ')
        elif message.caption:
            detected_title = message.caption.split('\n')[0]
            
        file_info = bot.get_file(file_id)
        video_link = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    
    # अगर यूजर ने टेक्स्ट लिंक भेजा है
    elif message.text and message.text.startswith('http'):
        video_link = message.text.strip()
        detected_title = video_link.split('/')[-1].split('?')[0].replace('_', ' ').replace('-', ' ')
        if not detected_title or len(detected_title) < 3:
            detected_title = "Web Uploaded Movie"

    if not video_link:
        bot.reply_to(message, "⚠️ कृपया अपने प्राइवेट चैनल से वीडियो सीधे इस बॉट पर **Forward** करें।")
        return

    # सही और साफ़-सुथरा डेटा स्ट्रक्चर (फर्जी वैल्यूज हटाई गईं)
    movie_data = {
        "ID": "M" + str(abs(hash(video_link)) % (999 - 100 + 1) + 100),
        "Title": detected_title.title(), # आटोमेटिक सही नाम कैपिटल फॉर्मेट में
        "Thumbnail_URL": "https://img.com/default_thumb.jpg",
        "Banner_URL": "https://img.com/default_banner.jpg",
        "Stream_URL": video_link,
        "Download_URL": video_link,
        "Category": "Full Movie / Series",
        "Industry": "Bollywood / Hollywood",
        "Language": "Hindi",
        "Quality": "1080p",
        "Show_in_Banner": "TRUE",
        "Views": "0",
        "Duration_or_Year": "2026",
        "Description": "शब् सिनेमा बॉट द्वारा जोड़ी गई फाइल।"
    }

    # सबसे पहले Recent टैब में सेव करें
    save_to_google_sheet("Recent", movie_data)
    
    # डेटा को अस्थायी रूप से सेव रखना ताकि बटन दबाने पर दूसरे टैब में जा सके
    user_pending_data[message.chat.id] = movie_data

    # Telegram Inline Buttons (दूसरा टैब चुनने के लिए - Recent और Series दोनों उपलब्ध)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎬 Movies", callback_data="tab_Movies"),
        types.InlineKeyboardButton("📺 Series", callback_data="tab_Series"),
        types.InlineKeyboardButton("📺 TV Shows", callback_data="tab_TV_Shows"),
        types.InlineKeyboardButton("⭐ Old Is Gold", callback_data="tab_Old_Is_Gold"),
        types.InlineKeyboardButton("🔞 Adult", callback_data="tab_Adult"),
        types.InlineKeyboardButton("❌ बस Recent में रहने दें", callback_data="tab_Done")
    )

    bot.reply_to(
        message,
        f"✅ फाइल का नाम: **{detected_title.title()}**\n"
        f"📌 इसे **Recent** टैब में जोड़ दिया गया है।\n\n"
        f"अब बताएं, क्या आप इसे **Series** या किसी अन्य टैब में भी भेजना चाहते हैं?",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# 4. बटन क्लिक होने पर दूसरे टैब (जैसे Series) में डेटा सेव करना
@bot.callback_query_handler(func=lambda call: call.data.startswith('tab_'))
def handle_tab_selection(call):
    selected_tab = call.data.split("_")[1]
    chat_id = call.message.chat.id
    
    if selected_tab == "Done":
        bot.answer_callback_query(call.id, "प्रोसेस समाप्त!")
        bot.edit_message_text("👍 डेटा केवल Recent टैब में सुरक्षित है।", chat_id, call.message.message_id)
        if chat_id in user_pending_data:
            del user_pending_data[chat_id]
        return

    if chat_id in user_pending_data:
        movie_data = user_pending_data[chat_id]
        # जिस टैब पर क्लिक किया जाएगा (जैसे Series), डेटा उस टैब में चला जाएगा
        save_to_google_sheet(selected_tab, movie_data)
        bot.answer_callback_query(call.id, f"{selected_tab} टैब में जोड़ दिया गया!")
        bot.edit_message_text(f"✅ डेटा सफलतापूर्वक **{selected_tab}** टैब में भी जोड़ा जा चुका है!", chat_id, call.message.message_id, parse_mode="Markdown")
        del user_pending_data[chat_id]
    else:
        bot.answer_callback_query(call.id, "सत्र समाप्त हो गया, कृपया दोबारा वीडियो भेजें।")
        bot.edit_message_text("⚠️ सेशन एक्सपायर हो गया है। कृपया नया वीडियो भेजें।", chat_id, call.message.message_id)

print("Bot is running...")
bot.infinity_polling()
