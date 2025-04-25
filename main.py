import os
import telebot
import requests
import sqlite3
import logging
from telebot import types
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# Cargar variables de entorno
load_dotenv()

# Scopes necesarios para acceder a Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Configuración del bot y API
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_CENTROPSICONATY")  # Lee el token desde .env
API_KEY = os.getenv("API_KEY_WEATHER")  # Lee el token desde .env
DB_PATH = os.getenv("DB_PATH", "telegram_bot.db")  # Ruta de la base de datos desde .env
bot = telebot.TeleBot(TOKEN)
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather?'

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#Creacion de comandos simples como `/start` y `/help`
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Teclado personalizado para iniciar el bot."""
    # Crear el teclado
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_agendar = KeyboardButton('📅 Agendar cita')
    btn_servicios = KeyboardButton('ℹ️ Servicios')
    btn_contactar = KeyboardButton('💬 Contactar por WhatsApp')
    btn_sobre_nataly = KeyboardButton('👩‍⚕️ Sobre Nataly')
    btn_testimonios = KeyboardButton('📝 Testimonios')

    # Agregar los botones al teclado
    markup.add(btn_agendar, btn_servicios, btn_contactar, btn_sobre_nataly, btn_testimonios)

    # Enviar el mensaje con el teclado
    bot.send_message(
        message.chat.id,
        "¡Hola! Bienvenido al bot del Consultorio Psicologico CentroPsicoNaty de Nataly Atuncar. Por favor selecciona una opción:",
        reply_markup=markup
    )

#INICIO - AGENDAR CITA
@bot.message_handler(func=lambda message: message.text == '📅 Agendar cita')
def handle_agendar_cita(message):
    """Solicitar al usuario el día y la hora para agendar una cita."""
    bot.reply_to(message, "¡Claro! Por favor, indícame el día y la hora en el formato 'AAAA-MM-DD HH:MM' (por ejemplo, 2025-04-25 10:00).")
    bot.register_next_step_handler(message, process_datetime)

def process_datetime(message):
    """Procesa el día y la hora proporcionados por el usuario."""
    try:
        # Convertir la entrada del usuario a un objeto datetime
        user_input = message.text.strip()
        start_time = datetime.strptime(user_input, "%Y-%m-%d %H:%M")
        end_time = start_time + timedelta(hours=1)  # Duración de 1 hora

        # Convertir a formato ISO 8601
        start_time_iso = start_time.isoformat()
        end_time_iso = end_time.isoformat()

        # Solicitar el correo de los asistentes
        bot.reply_to(message, "Por favor, proporciona los correos electrónicos de los asistentes separados por comas y sin espacios.")
        bot.register_next_step_handler(message, process_attendees, start_time_iso, end_time_iso)
    except ValueError:
        bot.reply_to(message, "El formato de fecha y hora no es válido. Por favor, usa el formato 'AAAA-MM-DD HH:MM'.")

def process_attendees(message, start_time_iso, end_time_iso):
    """Procesa los correos electrónicos de los asistentes y crea el evento."""
    try:
        # Obtener los correos electrónicos de los asistentes
        attendees = [email.strip() for email in message.text.split(",")]

        # Crear el evento en Google Calendar
        summary = "Cita con Nataly"
        description = "Cita agendada a través del bot de CentroPsicoNaty."
        event = create_event(summary, description, start_time_iso, end_time_iso, attendees)

        # Confirmar al usuario
        bot.reply_to(message, f"¡Cita creada con éxito! Aquí está el enlace: {event.get('htmlLink')}")
        
        # Mostrar nuevamente el teclado con las opciones
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn_agendar = KeyboardButton('📅 Agendar cita')
        btn_servicios = KeyboardButton('ℹ️ Servicios')
        btn_contactar = KeyboardButton('💬 Contactar por WhatsApp')
        btn_sobre_nataly = KeyboardButton('👩‍⚕️ Sobre Nataly')
        btn_testimonios = KeyboardButton('📝 Testimonios')

        # Agregar los botones al teclado
        markup.add(btn_agendar, btn_servicios, btn_contactar, btn_sobre_nataly, btn_testimonios)

        # Enviar el teclado al usuario
        bot.send_message(
            message.chat.id,
            "¿En qué más puedo ayudarte?",
            reply_markup=markup
        )

    except Exception as e:
        bot.reply_to(message, f"Hubo un error al crear la cita: {e}")
#FIN - AGENDAR CITA

#INICIO - SERVICIOS
@bot.message_handler(func=lambda message: message.text == 'ℹ️ Servicios')
def handle_servicios(message):
    """Muestra las opciones de servicios."""
    # Crear el teclado con las opciones de servicios
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_terapias = KeyboardButton('Lista de terapias')
    btn_video = KeyboardButton('Video explicativo')
    btn_precios = KeyboardButton('Precios y promociones')
    btn_volver = KeyboardButton('⬅️ Volver al inicio')  # Botón para volver al inicio
    markup.add(btn_terapias, btn_video, btn_precios, btn_volver)

    # Enviar el mensaje con el teclado
    bot.send_message(
        message.chat.id,
        "Selecciona una opción para obtener más información sobre nuestros servicios:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == 'Lista de terapias')
def handle_lista_terapias(message):
    """Muestra la lista de terapias disponibles."""
    bot.send_message(
        message.chat.id,
        "Ofrecemos las siguientes terapias:\n"
        "- Humanista\n"
        "- Cognitivo-Conductual\n"
        "- Parejas"
    )
    mostrar_teclado_inicio(message)

@bot.message_handler(func=lambda message: message.text == 'Video explicativo')
def handle_video_explicativo(message):
    """Muestra un video explicativo sobre cómo funciona una sesión."""
    bot.send_message(
        message.chat.id,
        "¿Cómo funciona una sesión? Mira este video explicativo: https://www.youtube.com/watch?v=ehRgWj5Yt7U"
    )
    mostrar_teclado_inicio(message)

@bot.message_handler(func=lambda message: message.text == 'Precios y promociones')
def handle_precios_promociones(message):
    """Muestra los precios y promociones disponibles."""
    bot.send_message(
        message.chat.id,
        "Nuestros precios y promociones:\n"
        "- Precio por consulta de 1 hora: 50 soles.\n"
        "- Pack de 4 sesiones con 10% de descuento."
    )
    mostrar_teclado_inicio(message)

@bot.message_handler(func=lambda message: message.text == '⬅️ Volver al inicio')
def handle_volver_inicio(message):
    """Vuelve al teclado inicial."""
    mostrar_teclado_inicio(message)

def mostrar_teclado_inicio(message):
    """Muestra el teclado inicial con las opciones principales."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_agendar = KeyboardButton('📅 Agendar cita')
    btn_servicios = KeyboardButton('ℹ️ Servicios')
    btn_contactar = KeyboardButton('💬 Contactar por WhatsApp')
    btn_sobre_nataly = KeyboardButton('👩‍⚕️ Sobre Nataly')
    btn_testimonios = KeyboardButton('📝 Testimonios')

    # Agregar los botones al teclado
    markup.add(btn_agendar, btn_servicios, btn_contactar, btn_sobre_nataly, btn_testimonios)

    # Enviar el teclado al usuario
    bot.send_message(
        message.chat.id,
        "¿En qué más puedo ayudarte?",
        reply_markup=markup
    )
#FIN - SERVICIOS

#INICIO - ENVIAR MENSAJE POR WHATSAPP
@bot.message_handler(func=lambda message: message.text == '💬 Contactar por WhatsApp')
def handle_contactar_whatsapp(message):
    """Envía un enlace para contactar a Nataly por WhatsApp."""
    whatsapp_number = "+51947203044"
    whatsapp_message = "¡Hola! Me gustaría obtener más información sobre los servicios del CentroPsicoNaty."
    whatsapp_link = f"https://wa.me/{whatsapp_number[1:]}?text={requests.utils.quote(whatsapp_message)}"

    bot.send_message(
        message.chat.id,
        f"Puedes contactar a Nataly por WhatsApp usando el siguiente enlace:\n{whatsapp_link}"
    )
#FIN - ENVIAR MENSAJE POR WHATSAPP

#INICIO - SOBRE NATALY
@bot.message_handler(func=lambda message: message.text == '👩‍⚕️ Sobre Nataly')
def handle_sobre_nataly(message):
    """Muestra información sobre Nataly."""
    # Ruta de la foto de Nataly
    photo_path = "FotoNataly.jpg"
    
    try:
        # Enviar la foto con el mensaje inicial
        with open(photo_path, 'rb') as photo:
            bot.send_photo(
                message.chat.id,
                photo,
                caption="Soy la Psicóloga Nataly Atuncar, especialista en Humanista y parejas."
            )
        
        # Enviar el mensaje de certificaciones
        bot.send_message(
            message.chat.id,
            "Certificaciones: Colegiada en CRP-12345"
        )
        
        # Enviar el enlace de LinkedIn
        bot.send_message(
            message.chat.id,
            "Puedes conocer más sobre mí en mi perfil de LinkedIn:\nwww.linkedin.com/in/jsilvaal"
        )
    except FileNotFoundError:
        bot.send_message(
            message.chat.id,
            "Lo siento, no se encontró la foto de Nataly. Por favor, verifica que el archivo 'FotoNataly.jpg' esté en el directorio correcto."
        )
#FIN - SOBRE NATALY

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

################################
@bot.message_handler(commands=['reunion'])
def schedule_meeting(message):
    """Programa una reunión en Google Calendar."""
    try:
        summary = "Reunión con el equipo"
        description = "Revisión semanal del proyecto."
        start_time = "2025-04-25T10:00:00-07:00"
        end_time = "2025-04-25T11:00:00-07:00"
        attendees = ["therock21@gmail.com", "therock21@hotmail.com"]

        event = create_event(summary, description, start_time, end_time, attendees)
        bot.reply_to(message, f"Reunión creada: {event.get('htmlLink')}")
    except Exception as e:
        bot.reply_to(message, f"Error al programar la reunión: {e}")

def authenticate_google():
    """Autentica al usuario con Google y devuelve un servicio de la API de Calendar."""
    creds = None
    # Archivo token.json para almacenar las credenciales del usuario
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # Si no hay credenciales válidas, solicita al usuario que inicie sesión
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        # Guarda las credenciales para futuras ejecuciones
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def create_event(summary, description, start_time, end_time, attendees=None):
    """Crea un evento en Google Calendar."""
    try:
        service = authenticate_google()
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Lima',  # Cambia a tu zona horaria
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Lima',
            },
            'attendees': [{'email': email} for email in attendees] if attendees else [],
        }
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Evento creado: {event_result.get('htmlLink')}")
        return event_result
    except Exception as e:
        print(f"Error al crear el evento: {e}")

if __name__ == '__main__':
    bot.polling(none_stop=True)
