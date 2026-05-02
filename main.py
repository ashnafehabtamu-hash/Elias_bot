import telebot
from telebot import types
import random
import os
from flask import Flask
from threading import Thread

# --- ማስተካከያ ---
TOKEN = "8614285319:AAGsvFYuLPkNI89uZxm1e3KVDPK9UhxAzQE"
ADMIN_ID = 8126126602  
bot = telebot.TeleBot(TOKEN)

# ለ Render እንዲመች (Keep-alive)
app = Flask('')
@app.route('/')
def home(): return "ቦቱ እየሰራ ነው!"

def run(): app.run(host='0.0.0.0', port=8080)

# ዳታቤዝ
user_data = {}
all_users = set()

CARS = {
    "🚛 Sino Truck": "3000 ETB",
    "🚚 Isuzu": "2500 ETB",
    "🚗 Toyota": "2000 ETB",
    "🚛 Iveco": "3000 ETB"
}

# --- ኪቦርዶች ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚗 መኪና መምረጥ", "📞 እርዳታ")
    return markup

def car_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for car in CARS.keys():
        markup.add(car)
    markup.add("🔙 ወደ ኋላ")
    return markup

# --- የቦቱ ስራ ---

@bot.message_handler(commands=['start'])
def start(message):
    all_users.add(message.chat.id)
    bot.send_message(message.chat.id, "እንኳን ወደ ግዛቸው የመኪና እጣ መቁረጫ በደህና መጡ! 🎫🚗", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🚗 መኪና መምረጥ")
def show_cars(message):
    msg = "እባክዎ የሚፈልጉትን የመኪና አይነት ይምረጡ፡\n\n"
    for car, price in CARS.items():
        msg += f"{car} --- {price}\n"
    bot.send_message(message.chat.id, msg, reply_markup=car_menu())

@bot.message_handler(func=lambda m: m.text in CARS.keys())
def get_car(message):
    user_data[message.chat.id] = {'car': message.text}
    bot.send_message(message.chat.id, "👤 እባክዎ ሙሉ ስምዎን ያስገቡ (3 ቃላት መሆን አለበት)፦", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 ወደ ኋላ"))
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    if message.text == "🔙 ወደ ኋላ": return start(message)
    name_parts = message.text.split()
    if len(name_parts) != 3:
        bot.send_message(message.chat.id, "⚠️ ስህተት፡ እባክዎ 3 ቃላት የተጠቀመ ሙሉ ስም ያስገቡ!")
        bot.register_next_step_handler(message, get_name)
        return
    user_data[message.chat.id]['name'] = message.text
    bot.send_message(message.chat.id, "📱 ስልክ ቁጥርዎን ያስገቡ (10 አሃዝ)፦")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    if message.text == "🔙 ወደ ኋላ": return start(message)
    phone = message.text
    if not (phone.isdigit() and len(phone) == 10):
        bot.send_message(message.chat.id, "⚠️ ስህተት፡ እባክዎ በትክክል 10 አሃዝ ስልክ ቁጥር ያስገቡ!")
        bot.register_next_step_handler(message, get_phone)
        return
    user_data[message.chat.id]['phone'] = phone
    
    pay_msg = f"💳 የክፍያ መረጃ\n\n" \
              f"📱 Telebirr: 0954873497\n" \
              f"🏦 CBE: 1000536009276\n\n" \
              f"እባክዎ የከፈሉበትን የደረሰኝ ፎቶ (Screenshot) ይላኩ። 📸"
    bot.send_message(message.chat.id, pay_msg)
    bot.register_next_step_handler(message, get_screenshot)

def get_screenshot(message):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "⚠️ እባክዎ የደረሰኝ ፎቶ (Screenshot) ብቻ ይላኩ!")
        bot.register_next_step_handler(message, get_screenshot)
        return
    
    user_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Verify & Send Ticket", callback_data=f"verify_{user_id}"))
    
    admin_info = f"🔔 አዲስ ክፍያ!\n👤 ስም: {user_data[user_id]['name']}\n📱 ስልክ: {user_data[user_id]['phone']}\n🚗 መኪና: {user_data[user_id]['car']}\n🆔 ID: {user_id}"
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_info, reply_markup=markup)
    bot.send_message(user_id, "✅ መረጃዎ ለአስተዳዳሪ ተልኳል። ሲረጋገጥ ቲኬት ይላክላችኋል።", reply_markup=main_menu())

# --- አስተዳዳሪ ማረጋገጫ ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('verify_'))
def verify_payment(call):
    user_id = int(call.data.split('_')[1])
    ticket_no = random.randint(1, 1000)
    
    success_msg = f"✅ ክፍያዎ ተረጋግጧል!\n\n👤 ስም: {user_data[user_id]['name']}\n🎫 የዕጣ ቁጥርዎ: {ticket_no}\n🚗 መኪና: {user_data[user_id]['car']}\n\nመልካም ዕድል! 🍀"
    bot.send_message(user_id, success_msg)
    bot.edit_message_caption(call.message.caption + f"\n\n✅ ተረጋግጧል! ቲኬት #{ticket_no}", ADMIN_ID, call.message.id)

# --- Broadcast ---
@bot.message_handler(commands=['post'], func=lambda m: m.chat.id == ADMIN_ID)
def start_broadcast(message):
    bot.send_message(ADMIN_ID, "ለሁሉም የሚላክ ጽሁፍ ወይም ፎቶ ይላኩ።")
    bot.register_next_step_handler(message, do_broadcast)

def do_broadcast(message):
    for user in all_users:
        try:
            if message.content_type == 'text': bot.send_message(user, message.text)
            elif message.content_type == 'photo': bot.send_photo(user, message.photo[-1].file_id, caption=message.caption)
        except: continue
    bot.send_message(ADMIN_ID, "መልዕክቱ ተልኳል!")

@bot.message_handler(func=lambda m: m.text == "🔙 ወደ ኋላ")
def go_back(message): start(message)

if __name__ == "__main__":
    Thread(target=run).start()
    print("ቦቱ ስራ ጀምሯል...")
    bot.infinity_polling()
