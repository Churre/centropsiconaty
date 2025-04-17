import telebot
from telebot import types

#Conexion con nuestro BOT
TOKEN = '7328298835:AAHar7LmiLhNCDMaF-DEUxSI_0Jjb0CG990'
bot = telebot.TeleBot(TOKEN)



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

if __name__ == '__main__':
    bot.polling(none_stop=True)