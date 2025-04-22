import os
import telebot
from telebot import types
from dotenv import load_dotenv
import requests
import sqlite3

load_dotenv()  # Carga las variables del archivo .env

#Conexion con nuestro BOT
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_CENTROPSICONATY")  # Lee el token desde .env
API_KEY = os.getenv("API_KEY_WEATHER")  # Lee el token desde .env
bot = telebot.TeleBot(TOKEN)
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather?'

def insert_user(telegram_id: int, name: str):
    conn = sqlite3.connect('telegram_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (telegram_id, name)
        VALUES (?, ?)
    ''', (telegram_id, name))
    conn.commit()
    cursor.close()
    conn.close()

@bot.message_handler(commands=['save'])
def save_user(message):
    telegram_id = message.from_user.id
    name = message.from_user.first_name
    insert_user(telegram_id, name)
    bot.reply_to(message, f'Bienvenido {name}, tu informacion ha sido guardada.')

def get_weather(city_name):
    complete_url = BASE_URL + "q=" + city_name + "&appid=" + API_KEY
    response = requests.get(complete_url)
    data = response.json()
    print(data)
    if data["cod"] != 404:
        main_data = data["main"]
        weather_data = data["weather"][0]
        temperature = main_data["temp"] - 273.15
        description = weather_data["description"]
        return f"Temperatura: {temperature:.2f}°C\n{description.capitalize()}"
    else:
        return 'Ciudad no encontrada'

@bot.message_handler(commands=['clima'])
def send_weather(message):
    city_name = message.text.split()[1] if len(message.text.split()) > 1 else None
    if city_name:
        weather_info = get_weather(city_name)
        bot.reply_to(message, weather_info)
    else:
        bot.reply_to(message, "Por favor, proporciona el nombre de la ciudad. Ejemplo: /clima Madrid")

#Creacion de comandos simples como `/start` y `/help`
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Hola! Soy tu primer bot creado con Telebot')

@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message, 'Puedes insteractuar conmigo usando comandos. Por ahora solo respondo a /start y /help')

#@bot.message_handler(func=lambda m: True)
#def echo_all(message):
#    bot.reply_to(message, message.text)

@bot.message_handler(commands=['pizza'])
def send_options(message):
    markup = types.InlineKeyboardMarkup(row_width=2)

    #Creando botones
    btn_si = types.InlineKeyboardButton('Si', callback_data='pizza_si')
    btn_no = types.InlineKeyboardButton('No', callback_data='pizza_no')

    #Agrega botones al markup
    markup.add(btn_si, btn_no)

    #Enviar mensajes con los botones
    bot.send_message(message.chat.id, "¿Te gusta la pizza?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call:True)
def callback_query(call):
    if call.data == 'pizza_si':
        bot.answer_callback_query(call.id, '¡A mi tambien!')
    elif call.data == 'pizza_no':
        bot.answer_callback_query(call.id, '¡Bueno cada uno tiene sus gustos!')

@bot.message_handler(commands=['foto'])
def send_image(message):
    img_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1200px-Python-logo-notext.svg.png'
    bot.send_photo(chat_id=message.chat.id, photo=img_url, caption='Aqui tienes tu imagen')

if __name__ == '__main__':
    bot.polling(none_stop=True)