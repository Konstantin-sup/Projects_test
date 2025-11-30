from http.client import responses
from locale import currency


import telebot
import requests
bot = telebot.TeleBot(TOKEN)
url_bin = "https://api.binance.com/api/v3/ticker/price?symbol="
crpt_url = "https://api.binance.com/api/v3/ticker/price"
list_24h = 'https://api.binance.com/api/v3/ticker/24hr'

def format_number(n):
    n = float(n)
    whole, frac = f"{n:.2f}".split(".")
    whole = '.'.join([whole[::-1][i:i+3] for i in range(0, len(whole), 3)])[::-1]
    return f"{whole}.{frac}"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я инфо-бот 😊\nВыберете команду")
    bot.send_message(message.chat.id, f"/info\n/crypto_price\n/crypto_list\n/top_growing\n/convert")

@bot.message_handler(commands=['info'])
def inf(message):
    with open('info.txt', encoding='utf-8') as f:
        bot.send_message(message.chat.id, f.read())


@bot.message_handler(commands=['crypto_list'])
def send_list(message):
    bot.send_message(message.chat.id, 'Отсортированный файл отправляеться')
    import csv
    response = requests.get(crpt_url)
    data = response.json()
    data_sorted_usdt = [pair for pair in data if pair["symbol"].endswith("USDT") and float(pair['price'])>0]
    final_product = sorted(data_sorted_usdt, key=lambda x: (float(x['price']), x['symbol']), reverse=True)
    with open('crypto.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['symbol', 'price'])
        writer.writeheader()
        for line in final_product:
            line['price'] = float(line['price'])
            writer.writerow(line)

    with open('crypto.csv', encoding='utf-8') as fl_out:
        bot.send_document(message.chat.id, fl_out)


@bot.message_handler(commands=['top_growing'])
def send_top(message):
    bot.send_message(message.chat.id, 'Файл с топ 10 ростущех криптовалют отправляеться')
    import json
    response = requests.get(list_24h)
    data = response.json()[:10]
    with open('top_growing.json', 'w' ,encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    with open('top_growing.json', encoding='utf-8') as fl_out:
        bot.send_document(message.chat.id, fl_out)


@bot.message_handler(commands=['crypto_price'])
def req(message):
    bot.send_message(message.chat.id, 'Отправьте пару криптовалюты в связке с USDT(Hапример: BTCUSDT)')
    bot.register_next_step_handler(message, anwser)  #ждет ответ пользователя и дает функции

def anwser(message):
    anw = message.text
    bot.send_message(message.chat.id, f'Полученя пара {anw}')
    response = requests.get(url_bin+anw.upper())
    data = response.json()
    if "code" in data and data["code"] < 0:
        bot.send_message(message.chat.id, 'Ошибка символа попрорбуйте ввести еще раз')
        bot.register_next_step_handler(message, anwser)

    else:
        bot.send_message(message.chat.id, f'{data['symbol']} - {round(float(data['price']), 2)} USDT (Binance)')


@bot.message_handler(commands=['convert'])
def take_name(message):
    bot.send_message(message.chat.id, f'Отправьте пару криптовалюты в связке с USDT(Hапример: BTCUSDT), ее количество, и валюту для конвертации(Например: EUR), через пробел в формате\n"НАЗВАНИЕ КОЛИЧЕСТВО ВАЛЮТА"')
    bot.register_next_step_handler(message, get_price)


def get_price(message):
    exchange_url = f"https://open.er-api.com/v6/latest/USD"
    bot.send_message(message.chat.id, 'Данные получены, идет обработка')

    try:
        
        try:
            name, value, currency_val = message.text.split()

        except ValueError:
            bot.send_message(message.chat.id,
                             f'Вы ввели недостаточно значений, введите запрос еще раз')
            bot.register_next_step_handler(message, get_price)
            return

        response_coin = requests.get(url_bin + name.upper()).json()
        if "code" in response_coin and response_coin["code"] < 0:
            bot.send_message(message.chat.id, f'Ошибка ввода названия криптоваляты(Your input:{name}), заполните запрос еще раз')
            bot.register_next_step_handler(message, get_price)
            return

        name_price = round(float(response_coin['price'])*float(value), 2) #price of 1 coin_name*value
        response_val = requests.get(exchange_url)
        price_f = format_number(round(response_val.json()['rates'][currency_val.upper()] * name_price, 2))
        bot.send_message(message.chat.id, f'Отлично, цена {value} {name.upper()}'
                                          f' в {currency_val.upper()} - {price_f} {currency_val.upper()}')

    except ValueError:
        bot.send_message(message.chat.id, f'Ошибка ввода цены криптоваляты(Your input:{value}) введите запрос еще раз')
        bot.register_next_step_handler(message, get_price)
        return

    except requests.exceptions.RequestException:
        bot.send_message(message.chat.id, "Ошибка сети! Попробуйте позже.")



@bot.message_handler(content_types=['text'])
def write_field(message):
    bot.send_message(message.chat.id, 'На данный момент понимаю только команды\n'
                                      '/info\n/crypto_price\n/crypto_list\n/top_growing\n/convert')

bot.polling()
