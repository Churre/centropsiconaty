import os
import telebot
from telebot import types
from dotenv import load_dotenv
import requests
import sqlite3
import logging

# Cargar variables de entorno
load_dotenv()

# Configuración del bot y API
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_CENTROPSICONATY")  # Lee el token desde .env
API_KEY = os.getenv("API_KEY_WEATHER")  # Lee el token desde .env
DB_PATH = os.getenv("DB_PATH", "telegram_bot.db")  # Ruta de la base de datos desde .env
bot = telebot.TeleBot(TOKEN)
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather?'

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def insert_user(telegram_id: int, name: str):
    """Inserta un usuario en la base de datos de manera segura."""
    if not isinstance(telegram_id, int) or not isinstance(name, str):
        raise ValueError("Datos inválidos para la inserción en la base de datos")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")  # Mejora la concurrencia
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (telegram_id, name)
                VALUES (?, ?)
            ''', (telegram_id, name))
            conn.commit()
            logging.info(f"Usuario {name} con ID {telegram_id} insertado correctamente.")
    except sqlite3.Error as e:
        logging.error(f"Error al insertar usuario: {e}")

@bot.message_handler(commands=['save'])
def save_user(message):
    """Guarda la información del usuario en la base de datos."""
    telegram_id = message.from_user.id
    name = message.from_user.first_name
    try:
        insert_user(telegram_id, name)
        bot.reply_to(message, f'Bienvenido {name}, tu información ha sido guardada.')
    except ValueError as e:
        bot.reply_to(message, f"Error: {e}")
    except Exception as e:
        bot.reply_to(message, "Ocurrió un error al guardar tu información.")
        logging.error(f"Error en save_user: {e}")

def get_weather(city_name):
    """Obtiene el clima de una ciudad usando la API de OpenWeather."""
    complete_url = BASE_URL + "q=" + city_name + "&appid=" + API_KEY
    try:
        response = requests.get(complete_url)
        data = response.json()
        if data["cod"] != 404:
            main_data = data["main"]
            weather_data = data["weather"][0]
            temperature = main_data["temp"] - 273.15
            description = weather_data["description"]
            return f"Temperatura: {temperature:.2f}°C\n{description.capitalize()}"
        else:
            return 'Ciudad no encontrada'
    except requests.RequestException as e:
        logging.error(f"Error al obtener el clima: {e}")
        return "No se pudo obtener la información del clima. Inténtalo más tarde."

@bot.message_handler(commands=['clima'])
def send_weather(message):
    """Envía el clima de una ciudad al usuario."""
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