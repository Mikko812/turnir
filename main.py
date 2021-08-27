from flask import Flask, render_template
import json
import threading
import telebot
import pandas as pd
from settings import BOWL_TOKEN, ADMIN_ID, TURNIR_DB
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from sql_db import SqlDb
from turnir_bp import db_to_df
from telebot import apihelper
apihelper.ENABLE_MIDDLEWARE = True
pd.set_option('display.max_columns', None)

DB = SqlDb('players.db')
TUR = SqlDb(TURNIR_DB)
db_init = TUR.convert_db_to_df()
db_to_df(db_init)
bot = telebot.TeleBot(BOWL_TOKEN)
THUMBUP = "\ud83d\udc4d".encode('utf-16', 'surrogatepass').decode('utf-16')
correct_result = 0
id_convert = {}


'''------- КЛАВИАТУРЫ -------'''
def admin_keyboard(admin_id):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.row("Записать игрока", "Записать результат")
    keyboard.row("Удалить игрока", "Изменить результат")
    keyboard.row("Список игроков", "Записать гандикап")
    bot.send_message(admin_id, 'Привет, Админ!', reply_markup=keyboard)


def player_keyboard_reg(player_id):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("Зарегистрироваться")
    msg = 'Чтобы зарегистрироваться нажмите кнопку или наберите /reg.'
    bot.send_message(player_id, msg, reply_markup=keyboard)


def player_keyboard_results(player_id):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("Результаты")
    bot.send_message(player_id, 'Нажав на кнопку "Результаты" или набрав /res Вы сможете посмотреть свои результаты.',
                     reply_markup=keyboard)


def res_inline_keyboard(player_id):
    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton("Отправить", callback_data='send')
    button2 = InlineKeyboardButton("Изменить", callback_data='correct')
    keyboard.add(button1, button2)
    bot.send_message(player_id, 'Выберите действие', reply_markup=keyboard)
'''КОНЕЦ КЛАВИАТУР'''


def show_table():
    tmp = TUR.convert_db_to_df()
    db_to_df(tmp)


def convert_id(player_name):
    pl_id = DB.get_player_by_name(player_name)
    tur_id = TUR.get_player_by_name(player_name)
    id_convert[pl_id] = tur_id
    print(id_convert)


# Разделение имени игрока и гандикапа
def reg_convert(message):
    if '.' in message.text:
        player_name = message.text.split('.')[0]
        handikap = int(message.text.split('.')[1])
    else:
        player_name = message.text
        handikap = 0
    return player_name, handikap


# Добавление нового игрока в базы игроков и турнира
def add_new_player_in_bd(message):
    print(2)
    player_id = message.from_user.id
    print(3)
    player_name, handikap = reg_convert(message)
    print(player_id)
    DB.add_new_player_in_db((player_id, player_name, handikap))
    TUR.add_new_player_in_db((player_id, player_name, handikap))
    show_table()
    bot.send_message(message.from_user.id, 'Вы зарегистрированы на турнир!', reply_markup=ReplyKeyboardRemove())
    bot.send_message(message.from_user.id, 'Удачи на турнире!', reply_markup=player_keyboard_results(player_id))


# Добавление нового игрока без телеги в базы игроков и турнира
def add_none_telegram_player_in_bd(message):
    player_name, handikap = reg_convert(message)
    player_id = DB.get_player_by_name(player_name)
    if player_id is None:
        DB.add_new_player_in_db((0, player_name, handikap))
        player_id = DB.get_player_by_name(player_name)
    TUR.add_new_player_in_db((player_id, player_name, handikap))
    bot.send_message(ADMIN_ID, f'Игрок {player_name} зарегистрирован на турнир!')
    show_table()


# Добавление результата игрока без телеги
def add_none_telegram_player_result(message):
    player_id = int(message.text.split('.')[0])
    result = int(message.text.split('.')[1])
    TUR.add_result_in_db(player_id, result)
    show_table()
    bot.send_message(ADMIN_ID, "Результат отправлен.")


# Изменение результата
def change_result(message):
    player_id = int(message.text.split('.')[0])
    game = message.text.split('.')[1]
    result = int(message.text.split('.')[2])
    TUR.change_result_in_db(player_id, game, result)
    bot.send_message(ADMIN_ID, 'Результат изменен')
    show_table()


def player_remove(message):
    player_id = int(message.text[:-1])
    TUR.remove_player_from_turnir(player_id)
    bot.send_message(ADMIN_ID, 'Игрок удален')
    db = TUR.convert_db_to_df()
    db_to_df(db)

def save_new_handikap(message):
    player_id = int(message.text.split('.')[0])
    handikap = int(message.text.split('.')[1])
    TUR.save_handikap(player_id, handikap)
    bot.send_message(ADMIN_ID, 'Гандикап изменен')
    db = TUR.convert_db_to_df()
    db_to_df(db)


# Замена текста на кнопках на команды
@bot.middleware_handler(update_types=['message'])
def commands_change(bot_instance, message):
    if message.text == 'Зарегистрироваться':
        message.text = '/reg'
    elif message.text == 'Результаты':
        message.text = '/res'
    elif message.text == 'Записать игрока':
        message.text = '/plsave'
    elif message.text == 'Записать результат':
        message.text = '/ressave'
    elif message.text == 'Удалить игрока':
        message.text = '/plremove'
    elif message.text == 'Изменить результат':
        message.text = '/reschange'
    elif message.text == 'Записать гандикап':
        message.text = '/handikap'
    elif message.text == 'Список игроков':
        message.text = '/players'


@bot.message_handler(commands=['players'])
def all_players(message):
    players = TUR.get_all_players()
    for p in players:
        bot.send_message(ADMIN_ID, p)


@bot.message_handler(commands=['handikap'])
def save_handikap(message):
    msg = bot.send_message(ADMIN_ID, 'Ввод с точкой: ID.ГАНДИКАП')
    bot.register_next_step_handler(msg, save_new_handikap)


@bot.message_handler(commands=['plremove'])
def remove_player(message):
    msg = bot.send_message(ADMIN_ID, 'Ввод с точкой: ID.')
    bot.register_next_step_handler(msg, player_remove)


@bot.message_handler(commands=['reschange'])
def result_change(message):
    msg = bot.send_message(ADMIN_ID, 'Ввод через точку: ID.ИГРА(1-4).РЕЗУЛЬТАТ')
    bot.register_next_step_handler(msg, change_result)


@bot.message_handler(commands=['plsave'])
def hand_save_player(message):
    msg = bot.send_message(ADMIN_ID, 'Ввод через точку: ФАМИЛИЯ ИМЯ.ГАНДИКАП (если есть)')
    bot.register_next_step_handler(msg, add_none_telegram_player_in_bd)


@bot.message_handler(commands=['ressave'])
def hand_save_player_result(message):
    msg = bot.send_message(ADMIN_ID, 'Ввод через точку: ID.РЕЗУЛЬТАТ')
    bot.register_next_step_handler(msg, add_none_telegram_player_result)


# Для всех игроков
@bot.message_handler(commands=['start'])
def start_message(message):
    msg = 'Боулинг-бот приветствует Вас! Расскажу немного о том, что Вы можете делать.'
    bot.send_message(message.from_user.id, msg)
    msg = '1. Регистрация. Нажмите внизу кнопку [Зарегистрироваться]. Если Вы первый раз у нас, ' \
          'то я попрошу Вас ввести (через точку) Фамилию Имя.Гандикап (если гандикап 0 - можно не вводить) ' \
          'и отправить сообщение как обычно через >. В следующий раз этого делать уже не нужно - регистрируемся ' \
          'только на турнир.'
    bot.send_message(message.from_user.id, msg)
    msg = '2. Запись результатов. Введите Ваш результат в игре и отправьте. Я попрошу Вас подтвердить его. ' \
          'Если всё верно, то нажмите кнопку [Отправить] - результат будет записан в таблицу. ' \
          'Если Вы ошиблись, то нажмите [Изменить] и наберите правильный результат. ' \
          'В ответ пришлю Ваш текущий средний.'
    bot.send_message(message.from_user.id, msg)
    msg = '3. Результаты. Внизу есть кнопка [Результаты]. Нажмите её и я пришлю все Ваши результаты на турнире.'
    bot.send_message(message.from_user.id, msg)
    player_keyboard_reg(message.from_user.id)


# Для администратора турнира
@bot.message_handler(commands=['admin'])
def start_message(message):
    if message.from_user.id == ADMIN_ID:
        admin_keyboard(message.from_user.id)


# Регистрация в системе и на турнир
@bot.message_handler(commands=['reg'])
def registration(message):
    player_id = message.from_user.id
    player_name = DB.get_player_by_id(player_id)
    if player_name is None:
        bot.send_message(message.from_user.id, 'Вас нет в системе.')
        msg = bot.send_message(message.from_user.id, 'Введите через точку: ФАМИЛИЯ ИМЯ.ГАНДИКАП (если есть):')
    else:
        msg = message
    bot.register_next_step_handler(msg, add_new_player_in_bd)


# Возвращение результатов игроку
@bot.message_handler(commands=['res'])
def send_results(message):
    player_id = message.from_user.id
    results = TUR.get_results(player_id)
    bot.send_message(message.from_user.id, f'Ваши результаты: {results}')


# Запись результатов игроков с телегой
@bot.message_handler(content_types=['text'])
def get_text(message):
    global correct_result
    if message.text.isdigit() and int(message.text) < 301:
        correct_result = int(message.text)
        res_inline_keyboard(message.from_user.id)
        if int(message.text) >= 250:
            bot.send_message(message.from_user.id, THUMBUP)
    elif '.' in message.text:
        add_none_telegram_player_result(message)
    else:
        bot.send_message(message.from_user.id, f'{message.text} - некорректный ввод...')


# Запись результата игрока с телегой (Inline)
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global correct_result
    try:
        if call.data == "send":
            player_name = DB.get_player_by_id(call.from_user.id)
            average = TUR.add_result_in_db(call.from_user.id, correct_result)
            bot.answer_callback_query(call.id, "Ваш результат отправлен.")
            if average == 0:
                bot.send_message(call.from_user.id, 'Вы уже сыграли все игры!')
            else:
                bot.send_message(call.from_user.id, f'Ваш средний: {average}')
            show_table()
        elif call.data == "correct":
            bot.answer_callback_query(call.id, "Наберите правильный результат")
    except Exception as e:
        print(repr(e))

def bot_start():
    bot.infinity_polling(timeout=30)

def flask_start():
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)

app = Flask(__name__)
#ssl = SSLify(app, methods=[])

@app.route('/')
def index():
    with open('table.json') as f:
        table = json.load(f)
    tab = list(table.values())
    return render_template('index.html', table=tab)

if __name__ == '__main__':
    t1 = threading.Thread(target=bot_start)
    t2 = threading.Thread(target=flask_start)
    t1.start()
    t2.start()
