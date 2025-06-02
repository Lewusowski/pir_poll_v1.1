
from flask import Flask
import telebot
from telebot import types
import csv
import os

app = Flask(__name__)

TOKEN = '8026901460:AAFUtnB52zXV4Gjxj-cW95EtM6hVunzhhgg' #'7905262846:AAF_7X8tsFmzfQIm_LPCR8u9Q3mIl53g5NY'
ADMIN_ID = 1508358992
RESULTS_FOLDER = 'survey_results'

os.makedirs(RESULTS_FOLDER, exist_ok=True)

bot = telebot.TeleBot(TOKEN)

QUESTIONS = [
    "Сколько Вам лет?",
    "Каков Ваш пол?",
    "К какому слою общества по доходу Вы себя относите?",
    "Сколько Вы зарабатываете в месяц?",
    "Имеете ли Вы недвижимость?",
    "Есть ли у Вас автомобиль?",
    "Сколько денег Вам нужно для жизни в месяц?",
    "Какую минимальную потерянную купюру в рублях Вы поднимите с земли?",
    "Вы нашли спрятанные деньги с визиткой хозяина. Какую минимальную сумму вы не вернете?",
    "За сколько Вы убьёте человека?",
    "За сколько денег Вы бы перестали работать?",
    "После какой суммы денег их прибавок не имеет значение?"
]

ANSWERS = {
    0: ["От 15-18 лет", "От 19-25 лет", "От 25-45 лет", "От 46 и более лет"],
    1: ["Мужской пол", "Женский пол"],
    2: ["К бедному слою населения",
        "К среднему слою населения", "К богатому слою населения", "К очень богатому слою населения"],
    3: ["Меньше 50.000 руб", "От 50.000 до 100.0000 руб",
        "От 100.000 до 250.000 руб", "От 250.000 до 500.000 руб", "От 500.000 руб"],
    4: ["Да, у меня есть недвижимость", "Нет, у меня нет недвижимости"],
    5: ["Да, у меня есть автомобиль!", "Нет, у меня нет автомобиля"],
    6: ["40.000 рублей", "60.000 рублей", "100.000 рублей", "150.000 рублей", ">= 200.000 рублей"],
    7: ["Номиналом в 50 рублей", "Номиналом в 100 рублей", "Номиналом в 1000 рублей", "Номиналом в 5000 рублей",
        "Не подниму"],
    8: ["Я верну всё, что нашёл", "Я не верну 50 рублей", "Я не верну 100 рублей", "Я не верну 1000 рублей",
        "Я не верну 5000 рублей", "Я не верну ни копейки!"],
    9: ["Более 100.000 руб", "Более 1.000.000 руб", "Более 10.000.000 руб", "Более 100.000.000 руб",
        "Более 1.000.000.000 руб", "Я ни за что не убью человека!"],
    10: ["За 500.000 рублей", "За 1.000.000 рублей", "За 5.000.0000 рублей", "За 10.000.000 рублей",
         "За >= 15.000.000 рублей"],
    11: ["Около 1.000.000 руб", "Около 5.000.000 руб", "Около 10.000.000 руб", "Около 100.000.000 руб",
         "Около 1.000.000.000 руб", "Около 10.000.000.000 руб"]
}

users = {}

def clean_chat(chat_id, message_ids):
    for msg_id in message_ids:
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение {msg_id}: {e}")

def create_inline_keyboard(question_index):
    markup = types.InlineKeyboardMarkup()
    for answer in ANSWERS.get(question_index, []):
        callback_data = f"ans_{question_index}_{answer}"
        markup.add(types.InlineKeyboardButton(text=answer, callback_data=callback_data))
    return markup

def save_results(user_id):
    if user_id not in users or not users[user_id].get('responses'):
        return None

    try:
        final_responses = []
        for i in range(len(QUESTIONS)):
            answer = users[user_id]['responses'].get(i, "Нет ответа")
            clean_answer = str(answer).replace('\n', ' ').strip()
            final_responses.append(clean_answer)

        filename = os.path.join(RESULTS_FOLDER, f"user_{user_id}.csv")

        with open(filename, "w", newline="", encoding="cp1251") as csvfile:
            writer = csv.writer(csvfile, dialect='excel', delimiter=';')
            writer.writerow(final_responses)

        return filename
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return None

def show_question(user_id, chat_id, question_index):
    question_text = f"❓ Вопрос {question_index+1}:\n\n{QUESTIONS[question_index]}"
    markup = create_inline_keyboard(question_index)
    msg = bot.send_message(chat_id, question_text, reply_markup=markup)
    users[user_id].setdefault('message_ids', []).append(msg.message_id)

def create_question_selector(user_id):
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for i in range(len(QUESTIONS)):
        if i not in users.get(user_id, {}).get('answered', []):
            buttons.append(types.InlineKeyboardButton(text=f"Вопрос {i+1}", callback_data=f"q_{i}"))
    for i in range(0, len(buttons), 3):
        markup.add(*buttons[i:i+3])
    return markup

@bot.message_handler(commands=['start', 'help'])
def start_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id in users and 'message_ids' in users[user_id]:
        clean_chat(chat_id, users[user_id]['message_ids'])
        users[user_id]['message_ids'] = []

    if user_id not in users:
        users[user_id] = {'answered': [], 'responses': {}, 'message_ids': []}
    else:
        users[user_id]['message_ids'] = []

    if len(users[user_id]['answered']) == len(QUESTIONS):
        msg = bot.send_message(chat_id, "🎉 Вы уже завершили опрос! Спасибо за участие!")
        users[user_id]['message_ids'].append(msg.message_id)
    else:
        msg = bot.send_message(
            chat_id,
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "Я провожу небольшой опрос в рамках исследования вопроса стоимости денег.\n"
            "Ответьте на несколько вопросов - это займет 2-3 минуты.\n\n"
            "Ваши ответы анонимны и используются только для статистики.\n\n"
            "👇 Выберите вопрос для ответа:",
            reply_markup=create_question_selector(user_id)
        )
        users[user_id]['message_ids'].append(msg.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if user_id in users and 'message_ids' in users[user_id]:
        clean_chat(chat_id, users[user_id]['message_ids'])
        users[user_id]['message_ids'] = []

    if user_id not in users:
        users[user_id] = {'answered': [], 'responses': {}, 'message_ids': []}

    if call.data.startswith('q_'):
        question_index = int(call.data.split('_')[1])
        show_question(user_id, chat_id, question_index)

    elif call.data.startswith('ans_'):
        _, q_index, answer = call.data.split('_', 2)
        q_index = int(q_index)

        users[user_id]['answered'].append(q_index)
        users[user_id]['responses'][q_index] = answer

        msg = bot.send_message(
            chat_id,
            f"✅ Вы ответили на вопрос {q_index+1}:\n"
            f"«{QUESTIONS[q_index]}»\n\n"
            f"Ваш ответ: {answer}"
        )
        users[user_id]['message_ids'].append(msg.message_id)

        if len(users[user_id]['answered']) == len(QUESTIONS):
            filename = save_results(user_id)

            msg = bot.send_message(
                chat_id,
                "🎉 Спасибо! Вы завершили опрос!\n"
                "Ваши ответы сохранены анонимно."
            )
            users[user_id]['message_ids'].append(msg.message_id)

            if filename and os.path.exists(filename):
                try:
                    with open(filename, 'rb') as f:
                        bot.send_document(ADMIN_ID, f, caption=f"Новый опрос от user_{user_id}")
                except Exception as e:
                    print(f"Ошибка отправки файла: {e}")
        else:
            msg = bot.send_message(
                chat_id,
                "👇 Выберите следующий вопрос:",
                reply_markup=create_question_selector(user_id)
            )
            users[user_id]['message_ids'].append(msg.message_id)

    bot.answer_callback_query(call.id)

'''
@app.route('/')
def launch():
    print("Working...")
    bot.infinity_polling()
'''

if __name__ == '__main__':
    app.run(debug = True, port = 8000)
