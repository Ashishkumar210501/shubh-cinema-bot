import os
import requests
import telebot
from telebot import types
import threading
import time

# आपका Telegram Bot Token यहाँ सेट है
BOT_TOKEN = "9203802169:AAEPHn1B8-bVyaY0jOfP8sXz-ekabmVP8l8"

# आपका Google Apps Script Web App URL
GAS_URL = "https://script.google.com/macros/s/AKfycbxggQxs77zEJt_7aa4IUfRPA5cQi-aYfEjsq9-FqMDv_cQz_F-mw2XqMP2RNslVQcTnMA/exec"

# आपकी Filemoon API Key
FILEMOON_API_KEY = "1666910y1zglkkt8t55493"

bot = telebot.TeleBot(BOT_TOKEN)

# अस्थाई रूप से यूजर का डेटा स्टोर करने के लिए डिक्शनरी
user_pending_data = {}

# 1. /start कमांड और रिप्लाई कीबोर्ड बटन्स
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
        "🎬 किसी भी मूवी या वीडियो का डायरेक्ट लिंक, Google Drive लिंक, या वीडियो फाइल यहाँ भेजें।\n"
        "बॉट उसे Filemoon पर अपलोड करके **Recent** टैब में जोड़ देगा।",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# 2. Filemoon पर वीडियो रिमोट अपलोड करने का फंक्शन
def upload_to_filemoon(video_url):
    api_url = f"https://filemoonapi.com/api/upload/url?key={FILEMOON_API_KEY}&url={video_url}"
    try:
        response = requests.get(api_url, timeout=30)
        data = response.json()
        if data.get("status") == 200:
            file_code = data["result"]["file_code"]
            stream_url = f"https://filemoon.sx/e/{file_code}"
            download_url = f"https://filemoon.sx/d/{file_code}"
            return stream_url, download_url
        else:
            print(f"Filemoon API Response Error: {data}")
    except Exception as e:
        print(f"Filemoon Connection Error: {e}")
    return None, None

# 3. Google Sheet (Google Apps Script) में डेटा भेजने का फंक्शन
def save_to_google_sheet(sheet_name, data_dict):
    payload = {
        "action": "addData",
        "sheetName": sheet_name,
        "data": data_dict
    }
    try:
        response = requests.post(GAS_URL, json=payload)
        return response.json()
    except Exception as e:
        print(f"Sheet Error: {e}")
        return {"status": "error"}

# 4. जब एडमिन कोई वीडियो लिंक या फाइल भेजे
@bot.message_handler(content_types=['text', 'video', 'document'])
def handle_incoming_content(message):
    if message.text in ["🎬 Add Movie", "🔥 Add Recent", "📺 Add Series", "📺 Add TV Show", "⏳ Old Is Gold", "🔞 Adult"]:
        bot.reply_to(message, "📌 कृपया इस टैब में जोड़ने के लिए उस मूवी/वीडियो का **लिंक या फाइल** भेजें:")
        return

    video_link = None
    
    # टेक्स्ट लिंक चेक करें
    if message.text and message.text.startswith('http'):
        video_link = message.text.strip()
    
    # डायरेक्ट वीडियो या डॉक्यूमेंट चेक करें
    elif message.video or message.document:
        file_id = message.video.file_id if message.video else message.document.file_id
        file_info = bot.get_file(file_id)
        video_link = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    
    if not video_link:
        bot.reply_to(message, "⚠️ कृपया कोई वैध वीडियो लिंक (URL) या वीडियो फाइल भेजें।")
        return

    # 🟢 Google Drive लिंक को ऑटोमैटिक डायरेक्ट डाउनलोड लिंक में बदलना
    if "drive.google.com" in video_link:
        try:
            if "/file/d/" in video_link:
                file_id = video_link.split("/file/d/")[1].split("/")[0]
                video_link = f"https://drive.google.com/uc?export=download&id={file_id}"
        except Exception as e:
            print(f"Drive Link Conversion Error: {e}")

    msg = bot.reply_to(message, "⏳ वीडियो Filemoon पर अपलोड हो रहा है, कृपया प्रतीक्षा करें...")
    
    # Filemoon Upload
    stream_url, download_url = upload_to_filemoon(video_link)
    
    if not stream_url:
        bot.edit_message_text("❌ Filemoon अपलोड विफल रहा!\nसुनिश्चित करें कि गूगल ड्राइव फाइल **'Anyone with the link' (Public)** हो।", message.chat.id, msg.message_id, parse_mode="Markdown")
        return

    # डेटा स्ट्रक्चर
    movie_data = {
        "ID": "M" + str(abs(hash(video_link)) % (999 - 100 + 1) + 100),
        "Title": "New Uploaded Video",
        "Thumbnail_URL": "https://img.com/default_thumb.jpg",
        "Banner_URL": "https://img.com/default_banner.jpg",
        "Stream_URL": stream_url,
        "Download_URL": download_url,
        "Category": "Action / Drama",
        "Industry": "Bollywood",
        "Language": "Hindi",
        "Quality": "1080p",
        "Show_in_Banner": "True",
        "Views": "0",
        "Duration_or_Year": "2026",
        "Description": "बॉट द्वारा ऑटो-अपलोड की गई मूवी।"
    }

    # सबसे पहले Recent टैब में सेव करें
    save_to_google_sheet("Recent", movie_data)
    
    # डेटा को अस्थायी रूप से सेव रखना
    user_pending_data[message.chat.id] = movie_data

    # Telegram Inline Buttons (दूसरा टैब चुनने के लिए)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎬 Movies", callback_data="tab_Movies"),
        types.InlineKeyboardButton("📺 Series", callback_data="tab_Series"),
        types.InlineKeyboardButton("📺 TV Shows", callback_data="tab_TV_Shows"),
        types.InlineKeyboardButton("⭐ Old Is Gold", callback_data="tab_Old_Is_Gold"),
        types.InlineKeyboardButton("🔞 Adult", callback_data="tab_Adult"),
        types.InlineKeyboardButton("❌ बस Recent में रहने दें", callback_data="tab_Done")
    )

    bot.edit_message_text(
        f"✅ वीडियो सफलतापूर्वक Filemoon पर अपलोड हो गया!\n"
        f"📌 इसे सबसे पहले **Recent** टैब में जोड़ दिया गया है।\n\n"
        f"अब बताएं, इसे और किस टैब में जोड़ना चाहते हैं?",
        message.chat.id,
        msg.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# 5. बटन क्लिक होने पर दूसरे टैब में डेटा सेव करना
@bot.callback_query_handler(func=lambda call: call.data.startswith('tab_'))
def handle_tab_selection(call):
    selected_tab = call.data.split("_")[1]
    chat_id = call.message.chat.id
    
    if selected_tab == "Done":
        bot.answer_callback_query(call.id, "प्रोसेस समाप्त!")
        bot.edit_message_text("👍 डेटा केवल Recent टैब में सुरक्षित कर दिया गया है।", chat_id, call.message.message_id)
        if chat_id in user_pending_data:
            del user_pending_data[chat_id]
        return

    if chat_id in user_pending_data:
        movie_data = user_pending_data[chat_id]
        save_to_google_sheet(selected_tab, movie_data)
        bot.answer_callback_query(call.id, f"{selected_tab} टैब में जोड़ दिया गया!")
        bot.edit_message_text(f"✅ डेटा सफलतापूर्वक **{selected_tab}** टैब में भी जोड़ा जा चुका है!", chat_id, call.message.message_id, parse_mode="Markdown")
        del user_pending_data[chat_id]
    else:
        bot.answer_callback_query(call.id, "सत्र समाप्त हो गया, कृपया दोबारा लिंक भेजें।")
        bot.edit_message_text("⚠️ सेशन एक्सपायर हो गया है। कृपया नई वीडियो लिंक भेजें।", chat_id, call.message.message_id)

# 6. Filemoon फाइलों को एक्टिव रखने का बैकग्राउंड फंक्शन (Pinger)
def background_link_pinger():
    while True:
        try:
            time.sleep(2592000) # हर 30 दिन में
            if GAS_URL:
                response = requests.get(GAS_URL + "?action=getAllLinks")
                data = response.json()
                for url in data.get("stream_urls", []):
                    if "filemoon" in url:
                        requests.get(url, timeout=10)
        except Exception as e:
            print(f"Background pinger error: {e}")

# बैकग्राउंड थ्रेड शुरू करना
ping_thread = threading.Thread(target=background_link_pinger, daemon=True)
ping_thread.start()

print("Bot is running...")
bot.infinity_polling()  # यहाँ स्पेस ठीक कर दिया गया है
