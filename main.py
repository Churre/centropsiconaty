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

        # Convertir a formato ISO 8601 con zona horaria
        start_time_iso = start_time.isoformat() + "-05:00"  # Zona horaria de Lima (UTC-5)
        end_time_iso = end_time.isoformat() + "-05:00"

        # Solicitar el correo de los asistentes
        bot.reply_to(message, "Por favor, proporciona los correos electrónicos de los asistentes separados por comas y sin espacios.")
        bot.register_next_step_handler(message, process_attendees, start_time_iso, end_time_iso)
    except ValueError:
        bot.reply_to(message, "El formato de fecha y hora no es válido. Por favor, usa el formato 'AAAA-MM-DD HH:MM'.")

def process_attendees(message, start_time_iso, end_time_iso):
    """Procesa los correos electrónicos de los asistentes y valida la disponibilidad antes de crear el evento."""
    try:
        # Obtener los correos electrónicos de los asistentes
        attendees = [email.strip() for email in message.text.split(",")]

        # Validar disponibilidad en Google Calendar
        if not is_time_available(start_time_iso, end_time_iso):
            # Obtener la fecha del evento
            date_iso = start_time_iso.split("T")[0]
            available_slots = get_available_slots(date_iso)

            if available_slots:
                bot.reply_to(
                    message,
                    f"Lo siento, ya hay una cita reservada en ese horario. Los horarios disponibles para el {date_iso} son:\n" +
                    "\n".join(available_slots) + "." + "\n" + "Por favor intenta agendar la cita de nuevo."
                )
            else:
                bot.reply_to(
                    message,
                    f"Lo siento, no hay horarios disponibles para el {date_iso}. Por favor intenta agendar la cita de nuevo."
                )
            mostrar_teclado_inicio(message)
            return

        # Crear el evento en Google Calendar
        summary = "Cita con Nataly"
        description = "Cita agendada a través del bot de CentroPsicoNaty."
        event = create_event(summary, description, start_time_iso, end_time_iso, attendees)

        # Confirmar al usuario
        bot.reply_to(message, f"¡Cita creada con éxito! Aquí está el enlace: {event.get('htmlLink')}")

        # Mostrar nuevamente el teclado con las opciones
        mostrar_teclado_inicio(message)

    except Exception as e:
        bot.reply_to(message, f"Hubo un error al crear la cita: {e}")

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

def is_time_available(start_time_iso, end_time_iso):
    """Verifica si hay disponibilidad en Google Calendar para el rango de tiempo dado."""
    try:
        service = authenticate_google()
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time_iso,
            timeMax=end_time_iso,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        # Si hay eventos en el rango de tiempo, no está disponible
        return len(events) == 0
    except Exception as e:
        print(f"Error al verificar disponibilidad: {e}")
        return False

def get_available_slots(date_iso):
    """Obtiene los horarios disponibles en Google Calendar para un día específico."""
    try:
        service = authenticate_google()
        # Definir el rango de tiempo del día (7:00 AM a 8:00 PM)
        start_of_day = f"{date_iso}T07:00:00-05:00"  # Inicio del día
        end_of_day = f"{date_iso}T20:00:00-05:00"  # Fin del día

        # Obtener eventos del día
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        # Crear una lista de horarios ocupados
        busy_slots = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            busy_slots.append((start, end))

        # Generar horarios disponibles
        available_slots = []
        current_time = datetime.strptime(start_of_day, "%Y-%m-%dT%H:%M:%S%z")
        end_time = datetime.strptime(end_of_day, "%Y-%m-%dT%H:%M:%S%z")

        for start, end in busy_slots:
            event_start = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
            if current_time < event_start:
                available_slots.append((current_time, event_start))
            current_time = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")

        # Agregar el último intervalo disponible si queda tiempo
        if current_time < end_time:
            available_slots.append((current_time, end_time))

        # Formatear los horarios disponibles
        formatted_slots = [
            f"{slot[0].strftime('%H:%M')} - {slot[1].strftime('%H:%M')}" for slot in available_slots
        ]
        return formatted_slots
    except Exception as e:
        print(f"Error al obtener horarios disponibles: {e}")
        return []
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

if __name__ == '__main__':
    bot.polling(none_stop=True)
