import sqlite3
import telebot
from telebot import types  # Импорт кнопок
from collections import defaultdict
import logging
from logging.handlers import RotatingFileHandler
import re
import os

API_TOKEN = 'ТОКЕН-СЮДА'  # Токен бота
AUTHORIZED_USERS = [2475526, 282944502, 1513301382]  # ID людей через запятую, у которых есть доступ администратора. Узнать свой ID https://t.me/myidbot
bot = telebot.TeleBot(API_TOKEN)
user_scores = defaultdict(int)

# Настройка логирования
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = RotatingFileHandler('bot.log', maxBytes=10240, backupCount=5, encoding='utf-8')  # 10 КБ на файл, максимум 5 файлов бэкапа
log_handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

def init_database(): #Функция инициализации базы данных
    conn = sqlite3.connect('user_scores.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scores
                 (username text PRIMARY KEY, score integer)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reasons
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, 
                  points INTEGER, 
                  reason TEXT)''') 
    conn.commit()
    conn.close()

def load_scores(): #Функия загрузки базы данных
    conn = sqlite3.connect('user_scores.db')
    c = conn.cursor()
    c.execute("SELECT * FROM scores")
    scores = c.fetchall()
    for username, score in scores:
        user_scores[username] = score
    conn.close()

def save_scores(): #Функия сохранения результатов в базу данных
    conn = sqlite3.connect('user_scores.db')
    c = conn.cursor()
    for username, score in user_scores.items():
        c.execute("INSERT OR REPLACE INTO scores VALUES (?, ?)", (username, score))
    conn.commit()
    conn.close()

# Инициализация базы данных и загрузка данных при запуске
init_database()
load_scores()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Создаём клавиатуру с одной кнопкой
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton(text="Посмотреть результаты")
    keyboard.add(button)

    # Отправляем сообщение с клавиатурой
    bot.reply_to(message, "Привет! Отправь мне юзернейм и очки в формате '@username +10 Причина' или '@username -10 Причина', чтобы обновить счет.", reply_markup=keyboard)

def delete_user(username):
    conn = sqlite3.connect('user_scores.db')
    c = conn.cursor()
    c.execute("DELETE FROM scores WHERE username=?", (username,))
    c.execute("DELETE FROM reasons WHERE username=?", (username,)) 
    conn.commit()
    conn.close()
    if username in user_scores:
        del user_scores[username]

def check_user_exists(username):
    conn = sqlite3.connect('user_scores.db')
    c = conn.cursor()
    c.execute("SELECT * FROM scores WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result is not None  # Возвращает True, если пользователь существует

@bot.message_handler(commands=['delete'])
def handle_delete(message):
    if message.from_user.id in AUTHORIZED_USERS:
        try:
            # Пытаемся получить username из команды (второе слово)
            username_to_delete = message.text.split()[1]
            logging.info(f"User @{message.from_user.username} {message.from_user.id} requested to delete user: {username_to_delete}")

            if check_user_exists(username_to_delete):
                delete_user(username_to_delete)
                bot.reply_to(message, f"Пользователь {username_to_delete} удален.")
            else:
                bot.reply_to(message, "Пользователь не найден.")

        except IndexError:
            # Если username не указан, выводим список пользователей с кнопками
            conn = sqlite3.connect('user_scores.db')
            c = conn.cursor()
            c.execute("SELECT username FROM scores")
            usernames = [row[0] for row in c.fetchall()]
            conn.close()

            if usernames:
                keyboard = types.InlineKeyboardMarkup()
                for username in usernames:
                    score = user_scores[username]  # Получаем количество баллов
                    button_text = f"{username} - {score}"  # Формируем текст кнопки
                    button = types.InlineKeyboardButton(text=button_text, callback_data=f"delete_{username}")
                    keyboard.add(button)
                bot.reply_to(message, "Выберите пользователя для удаления:", reply_markup=keyboard)
            else:
                bot.reply_to(message, "В базе данных нет пользователей.")

    else:
        bot.reply_to(message, "У вас нет прав для удаления пользователей.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
def handle_delete_callback(call):
    username_to_delete = call.data.split("_")[1]
    if check_user_exists(username_to_delete):
        delete_user(username_to_delete)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                              text=f"Пользователь {username_to_delete} удален.")
        logging.info(f"User @{call.from_user.username} {call.from_user.id} deleted user: {username_to_delete}")
    else:
        bot.answer_callback_query(call.id, text="Пользователь не найден.")

def clear_all_users():
    conn = sqlite3.connect('user_scores.db')
    c = conn.cursor()
    c.execute("DELETE FROM scores")
    c.execute("DELETE FROM reasons") 
    conn.commit()
    conn.close()
    user_scores.clear()  # Очищаем словарь user_scores

def check_log_size():
    log_size = os.path.getsize('bot.log')
    max_log_size = 10240  # 10 KB
    if log_size > max_log_size:
        with open('bot.log', 'w', encoding='utf-8'):
            pass  # Очищаем файл

@bot.message_handler(commands=['log_size'])
def handle_log_size(message):
    if message.from_user.id in AUTHORIZED_USERS:
        check_log_size()  # Выполняем проверку размера лога
        log_size = os.path.getsize('bot.log')
        bot.reply_to(message, f"Текущий размер лог-файла: {log_size} байт")
    else:
        bot.reply_to(message, "У вас нет прав для просмотра размера лог-файла.")

@bot.message_handler(commands=['clear_all'])
def handle_clear_all(message):
    if message.from_user.id in AUTHORIZED_USERS:
        keyboard = types.InlineKeyboardMarkup()
        confirm_button = types.InlineKeyboardButton(text="Да, очистить", callback_data="confirm_clear_all")
        cancel_button = types.InlineKeyboardButton(text="Отмена", callback_data="cancel_clear_all")
        keyboard.add(confirm_button, cancel_button)
        bot.reply_to(message, "Вы уверены, что хотите очистить весь список пользователей?", reply_markup=keyboard)
        logging.info(f"User @{message.from_user.username} {message.from_user.id} requested to clear all users")  # Логирование кто вызывал функцию очистки всех пользователей
    else:
        bot.reply_to(message, "У вас нет прав для очистки списка пользователей.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_clear_all"))
def handle_confirm_clear_all(call):
    clear_all_users()
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                          text="Список пользователей очищен.")
    logging.info(f"User @{call.from_user.username} {call.from_user.id} cleared all users.")  # Логирование кто очистил весь список пользователей

@bot.callback_query_handler(func=lambda call: call.data == "cancel_clear_all")
def handle_cancel_clear_all(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                          text="Очистка списка пользователей отменена.")
    logging.info(f"User @{call.from_user.username} {call.from_user.id} caused all users to be purged, but then canceled the action")  # Логирование кто вызвал очистку всех пользователей, но затем отменил

@bot.message_handler(func=lambda message: message.text == "Посмотреть результаты")
def handle_results_button(message):
    totals(message)  # Вызываем функцию totals напрямую

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def change_score(message):
    text_parts = message.text.split()
    if len(text_parts) >= 3 and (text_parts[1].startswith('+') or text_parts[1].startswith('-')):
        username = text_parts[0]
        points = int(text_parts[1])
        reason = " ".join(text_parts[2:])  # Get the reason from the rest of the message 

        # Проверка, авторизован ли пользователь
        if message.from_user.id in AUTHORIZED_USERS:
            # Сохранение информации о причине в базе данных
            conn = sqlite3.connect('user_scores.db')
            c = conn.cursor()
            c.execute("INSERT INTO reasons VALUES (?, ?, ?, ?)", (None, username, points, reason))  # ID автоинкрементируется
            conn.commit()
            conn.close()

            user_scores[username] += points
            logging.info(f"User @{message.from_user.username} {message.from_user.id} changed score for {username}: Points: {points}. Reason: {reason}") 
            bot.reply_to(message, f"Изменение счёта для {username}: {points}. Текущий счёт: {user_scores[username]}")
            save_scores()  # Сохраняем изменения в базе данных
        else:
            bot.reply_to(message, "У вас нет прав для изменения баллов.") 
    else:
        bot.reply_to(message, "Пожалуйста, отправьте сообщение в формате '@username +10 Причина' или '@username -10 Причина'.")

# Команда для просмотра истории изменений баллов пользователя
@bot.message_handler(commands=['history'])
def show_history(message):
    if message.from_user.id in AUTHORIZED_USERS:  # Проверка авторизации
        try:
            username = message.text.split()[1]
        except IndexError:
            bot.reply_to(message, "Укажите имя пользователя, например: /history @username")
            return

        conn = sqlite3.connect('user_scores.db')
        c = conn.cursor()
        c.execute("SELECT points, reason FROM reasons WHERE username=?", (username,))
        history = c.fetchall()
        conn.close()

        if history:
            history_message = f"История изменений баллов для {username}:\n"
            for points, reason in history:
                history_message += f"{'+' if points > 0 else ''}{points} - {reason}\n"
            bot.reply_to(message, history_message)
        else:
            bot.reply_to(message, f"История изменений баллов для {username} не найдена.")
    else:
        bot.reply_to(message, "У вас нет прав для просмотра истории изменений баллов.")

@bot.message_handler(commands=['totals'])
def totals(message):
    if not user_scores:
        bot.reply_to(message, "Пока никто не набрал очков.")
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button = types.KeyboardButton(text="Посмотреть результаты")
        keyboard.add(button)
    else:
        # Сортировка словаря по значениям (очкам) в порядке убывания
        sorted_scores = sorted(user_scores.items(), key=lambda item: item[1], reverse=True)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button = types.KeyboardButton(text="Посмотреть результаты")
        keyboard.add(button)

        totals_message = "🏆 Топ по баллам:\n"
        for username, score in sorted_scores:
            totals_message += f"{username}: {score}\n"
        
        bot.reply_to(message, totals_message)

@bot.message_handler(commands=['top10'])
def totals(message):
    if not user_scores:
        bot.reply_to(message, "Пока никто не набрал очков.")
    else:
        # Сортировка словаря по значениям (очкам) в порядке убывания
        sorted_scores = sorted(user_scores.items(), key=lambda item: item[1], reverse=True)

        # Берём только первые 10 элементов
        top_10_scores = sorted_scores[:10] 

        totals_message = "🏆 Топ 10 по баллам:\n"
        for username, score in top_10_scores:
            totals_message += f"{username}: {score}\n"
        bot.reply_to(message, totals_message)

@bot.message_handler(commands=['log'])
def handle_log(message):
    if message.from_user.id in AUTHORIZED_USERS:
        try:
            with open('bot.log', 'r', encoding='utf-8') as f:  # Add encoding='utf-8'
                log_content = f.read()

            # Получаем username из команды (если он есть)
            try:
                username_filter = message.text.split()[1]
            except IndexError:
                username_filter = None

            if log_content:
                # Фильтрация лога по username (если он указан)
                if username_filter:
                    filtered_lines = []
                    for line in log_content.splitlines():
                        if re.search(rf"{username_filter}", line):
                            filtered_lines.append(line)
                    log_content = "\n".join(filtered_lines)

                # Отправка лога по частям, если он слишком большой
                for chunk in telebot.util.split_string(log_content, 4096):
                    bot.send_message(message.chat.id, chunk)
            else:
                bot.reply_to(message, "Файл лога пуст.")
        except FileNotFoundError:
            bot.reply_to(message, "Файл лога не найден.")
    else:
        bot.reply_to(message, "У вас нет прав для просмотра логов.")

@bot.message_handler(commands=['points', 'score'])
def get_user_score(message):
    username = f"@{message.from_user.username}"  # Получаем имя пользователя с "@"
    if username in user_scores:  # Проверяем, есть ли пользователь в базе
        score = user_scores[username]  # Получаем количество очков
        bot.reply_to(message, f"Ваше текущее количество очков: {score}")
    else:
        bot.reply_to(message, "У вас пока нет очков.")

bot.polling()