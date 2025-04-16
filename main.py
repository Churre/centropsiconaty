import telebot

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

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, message.text)

if __name__ == '__main__':
    bot.polling(none_stop=True)