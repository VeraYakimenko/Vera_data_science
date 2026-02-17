import telebot
from extensions import Converter, APIException
from config import TOKEN  

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = '''Привет! Я умею конвертировать валюту.\n\n\
Отправьте сообщение в формате:\n\
<название валюты> <название валюты, в которую хотите перевести> <сумма>\n\n\
Например: EUR USD 100\n\n\
Также доступна команда /values для просмотра доступных валют.'''
    bot.reply_to(message, text)

@bot.message_handler(commands=['values'])
def list_available_currencies(message):
    text = 'Доступные валюты:\n- EUR (Евро)\n- USD (Доллар)\n- RUB (Рубль)'
    bot.reply_to(message, text)

@bot.message_handler(content_types=['text'])
def handle_converter(message):
    try:
        values = message.text.split(' ')
        if len(values) != 3:
            raise APIException('Нужно ввести ровно три параметра: <валюта> <валюта> <сумма>.')
        
        base, quote, amount = values
        result = Converter.get_price(base.upper(), quote.upper(), float(amount))
        text = f'Стоимость {amount} {base} составляет {result:.2f} {quote}.'
        bot.reply_to(message, text)
    except APIException as e:
        bot.reply_to(message, f'Ошибка пользователя: {e}')
    except Exception as e:
        bot.reply_to(message, f'Ошибка сервера: {e}')

bot.polling(none_stop=True)