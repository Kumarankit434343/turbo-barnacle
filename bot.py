import logging
import os
import sqlite3
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.utils.request import Request

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Telegram Bot Token - replace with your token
TOKEN = os.getenv('BOT_TOKEN', '8588967117:AAFzbGHkera-SCT5U6udPVB8hkAVAJKKb3I
')

# Set your webhook URL here (replace with your actual URL)
WEBHOOK_URL = 'https://yourdomain.com'  # <-- CHANGE THIS before deploy

bot = Bot(token=TOKEN, request=Request(con_pool_size=8))

conn = sqlite3.connect('botdata.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS users
(
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    bonus_claimed INTEGER DEFAULT 0,
    referrer_id INTEGER,
    referrals INTEGER DEFAULT 0,
    welcome_done INTEGER DEFAULT 0
)
''')
conn.commit()

def main_menu():
    keyboard = [
        [InlineKeyboardButton("Balance 🤑", callback_data='balance'),
         InlineKeyboardButton("Refer Earn 👥", callback_data='refer')],
        [InlineKeyboardButton("Bonus 🎁", callback_data='bonus'),
         InlineKeyboardButton("Withdraw 🤑💸", callback_data='withdraw')],
        [InlineKeyboardButton("Payout Method 🏦", callback_data='payout'),
         InlineKeyboardButton("Earn More 📍", callback_data='earnmore')]
    ]
    return InlineKeyboardMarkup(keyboard)


def add_user_if_new(user_id: int, referrer_id: int = None):
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    if not user:
        if referrer_id == user_id:
            referrer_id = None

        c.execute('INSERT INTO users(user_id, balance, bonus_claimed, referrer_id, referrals, welcome_done) VALUES (?,0,0,?,0,0)',
                  (user_id, referrer_id))
        conn.commit()

        if referrer_id:
            c.execute('SELECT * FROM users WHERE user_id = ?', (referrer_id,))
            if c.fetchone():
                c.execute('UPDATE users SET balance = balance + 2, referrals = referrals + 1 WHERE user_id = ?', (referrer_id,))
                conn.commit()


@app.route('/hook', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        handle_update(update)
        return 'OK', 200


def handle_update(update: Update):
    if update.message:
        message = update.message
        user_id = message.from_user.id

        if message.text and message.text.startswith('/start'):
            args = message.text.split()
            referrer_id = None
            if len(args) > 1:
                try:
                    referrer_id = int(args[1])
                except ValueError:
                    referrer_id = None

            c.execute('SELECT welcome_done FROM users WHERE user_id = ?', (user_id,))
            row = c.fetchone()

            if not row:
                add_user_if_new(user_id, referrer_id)
                c.execute('UPDATE users SET welcome_done = 1 WHERE user_id = ?', (user_id,))
                conn.commit()

                text = ("Welcome! Please join our official channel:\n"
                        "👉 https://t.me/v1r0us_Official\n\n"
                        "Use the menu below once done.")
                bot.send_message(chat_id=user_id, text=text, reply_markup=main_menu())

            else:
                bot.send_message(
                    chat_id=user_id,
                    text=f"Welcome back {message.from_user.first_name}! Use the menu below.",
                    reply_markup=main_menu()
                )

    elif update.callback_query:
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data

        if data == 'balance':
            c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            row = c.fetchone()
            balance = row[0] if row else 0
            bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=f"Your balance is: {balance} points.",
                reply_markup=main_menu()
            )

        elif data == 'refer':
            c.execute('SELECT referrals FROM users WHERE user_id = ?', (user_id,))
            row = c.fetchone()
            referrals = row[0] if row else 0

            bot_username = bot.get_me().username
            referral_link = f"https://t.me/{bot_username}?start={user_id}"

            text = (f"Your Referral Link:\n{referral_link}\n\n"
                    f"You have referred {referrals} users and earned {referrals * 2} points.")

            bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=text,
                reply_markup=main_menu()
            )

        elif data == 'bonus':
            c.execute('SELECT bonus_claimed FROM users WHERE user_id = ?', (user_id,))
            row = c.fetchone()
            if row and row[0] == 0:
                c.execute('UPDATE users SET bonus_claimed = 1 WHERE user_id = ?', (user_id,))
                conn.commit()
                bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id,
                    text="You have received 0 points as a one-time bonus 🎁.",
                    reply_markup=main_menu()
                )
            else:
                bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id,
                    text="You have already claimed your bonus.",
                    reply_markup=main_menu()
                )

        elif data == 'withdraw':
            bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="Withdraw feature coming soon!",
                reply_markup=main_menu()
            )

        elif data == 'payout':
            bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="Payout method feature coming soon!",
                reply_markup=main_menu()
            )

        elif data == 'earnmore':
            bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="Earn more feature coming soon!",
                reply_markup=main_menu()
            )


if __name__ == '__main__':
    print(f"Setting webhook to {WEBHOOK_URL}/hook ...")
    bot.set_webhook(WEBHOOK_URL + '/hook')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')))
