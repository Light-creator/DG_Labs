from flask import Flask, request, jsonify
from telebot.types import Update
import telebot
import sqlite3
import base64
import datetime
import os

from PIL import Image
import io

from passlib.hash import bcrypt
from datetime import datetime, timedelta
from dotenv import load_dotenv

import tensorflow as tf
import numpy as np
from keras.preprocessing import image

load_dotenv()

token = os.getenv("TOKEN")
db_name = os.getenv("DB_NAME")
model_file = os.getenv("MODEL")

print(token)

class Client:
    def __init__(self, user_tuple):
        self.id = user_tuple[0]
        self.chat_id = user_tuple[1]
        self.passwd = user_tuple[2]
        self.response_state = user_tuple[3]
        self.session_id = user_tuple[4]
        self.registered = user_tuple[5]
        self.logged_in = user_tuple[6]


class DBManager:
    def __init__(self):
        self.open_conn()      
        self.create_table()
        self.close_conn()

        
    def open_conn(self):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def close_conn(self):
        self.conn.close()

    def get_user(self, chat_id):
        self.open_conn()
        self.cursor.execute('SELECT * FROM Users WHERE chat_id = ?', (chat_id, ))
        res = self.cursor.fetchone()
        self.close_conn()
        
        if res == None: return None
        return Client(res)

    def create_table(self):
        self.cursor.execute('DROP TABLE Users')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY,
            chat_id TEXT NOT NULL,
            passwd TEXT,
            resp_state TEXT,
            session_id TEXT,
            registered INTEGER NOT NULL,
            logged_in INTEGER NOT NULL
            )
            ''')
    def update_resp_state(self, chat_id, resp_state):
        self.open_conn()
        self.cursor.execute("UPDATE Users SET resp_state = ? WHERE chat_id = ?", (resp_state, chat_id))
        self.conn.commit()
        self.close_conn()

    def update_passwd(self, chat_id, passwd):
        self.open_conn()
        self.cursor.execute("UPDATE Users SET passwd = ? WHERE chat_id = ?", (passwd, chat_id))
        self.conn.commit()
        self.close_conn()

    def update_logged_in(self, chat_id, logged_in: int):
        self.open_conn()
        self.cursor.execute("UPDATE Users SET logged_in = ? WHERE chat_id = ?", (logged_in, chat_id))
        self.conn.commit()
        self.close_conn()

    def update_registered(self, chat_id, registered: int):
        self.open_conn()
        self.cursor.execute("UPDATE Users SET registered = ? WHERE chat_id = ?", (registered, chat_id))
        self.conn.commit()
        self.close_conn()

    def update_session_id(self, chat_id, session_id):
        self.open_conn()
        self.cursor.execute("UPDATE Users SET session_id = ? WHERE chat_id = ?", (session_id, chat_id))
        self.conn.commit()
        self.close_conn()

    def add_user(self, chat_id):
        self.open_conn()
        self.cursor.execute('INSERT INTO Users (chat_id, logged_in, registered) VALUES (?, ?, ?)', (chat_id, 0, 0))
        self.conn.commit()
        self.close_conn()

    def reg_user(self, chat_id, hashed_passwd):
        self.open_conn()
        self.cursor.execute("UPDATE Users SET registered ?, passwd = ? WHERE chat_id = ?", (resp_state, hashed_passwd, chat_id))
        self.conn.commit()
        self.close_conn()


class State:
    def __init__(self):
        self.db = DBManager()
        self.model = tf.keras.models.load_model(model_file)

    def add_user(self, chat_id):
        if not self.is_user_exists(chat_id):
            self.db.add_user(chat_id)

    def is_user_exists(self, chat_id) -> bool:
        user = self.db.get_user(chat_id)
        return user != None

    def get_user(self, chat_id):
        return self.db.get_user(chat_id)

    def register(self, chat_id, passwd) -> (bool, str):
        user = self.get_user(chat_id)
        print(user.registered)
        if user.registered:
            return False, "You are already registered!"
        
        hashed_passwd = bcrypt.hash(passwd)
        self.db.update_passwd(chat_id, hashed_passwd)
        self.db.update_registered(chat_id, 1)

        return True, "You are successfully registered!"
    
    def get_session_id(self, chat_id):
        timestamp = datetime.now().isoformat().encode('utf-8')
        base64_timestamp = base64.b64encode(timestamp).decode('utf-8')
        return base64_timestamp

    def login(self, chat_id, passwd) -> (bool, str):
        self.add_user(chat_id)

        user = self.get_user(chat_id)
        if user.logged_in:
            return False, "You are already logged in"

        if not user.registered:
            return False, "You are not registered yet"
    
        if not bcrypt.verify(passwd, user.passwd):
            return False, "Incorrect password. Please, try againg!"
        
        session_id = self.get_session_id(chat_id)
        self.db.update_session_id(chat_id, session_id)
        self.db.update_logged_in(chat_id, 1)
        return True, "You are successfully logged_in"

    def get_response_state(self, chat_id) -> str:
        state.add_user(chat_id)
        user = state.get_user(chat_id)

        if user.response_state == None: return ""
        return user.response_state

    def set_response_state(self, chat_id, resp_state):
        self.db.update_resp_state(chat_id, resp_state)
    
    def check_registration(self, chat_id) -> (bool, str):
        user = self.db.get_user(chat_id)
        
        return None
    
    def session_expired(self, user) -> bool:
        if user.session_id == None:
            return True
        
        encoded = user.session_id
        print(encoded)
        decoded_bytes = base64.b64decode(encoded)
        epoch_time = decoded_bytes.decode('utf-8')
        dt = datetime.fromisoformat(epoch_time)
        
        now = datetime.now()
        if now - timedelta(hours=1) > dt:
            return True

        return False

    def check_auth(self, chat_id) -> (bool, str):
        user = self.get_user(chat_id)

        if not user.registered:
            return False, "You are not registered yet!"
        
        if not user.logged_in:
            return False, "You are not logged in!"
        
        if self.session_expired(user):
            self.update_logged_in(chat_id, 0)
            self.update_session_id(chat_id, "")
            return False, "Your session has expired. Please, log in again!"

        return True, "You are logged in!"

    def predict(self, path):
        img = image.load_img(path, target_size=(200, 200))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        images = np.vstack([x])
        classes = self.model.predict(images, batch_size=10)
        if classes[0]<0.5: return "human"
        else: return "monkey"


bot = telebot.TeleBot(token)

state = State()

@bot.message_handler(commands=["start"])
def start_message(msg):
    state.add_user(msg.chat.id)
    user = state.get_user(msg.chat.id)
    print(user.logged_in)
    bot.send_message(msg.chat.id, "Hello, Welcome!")

@bot.message_handler(commands=["register"])
def register(msg):
    state.add_user(msg.chat.id)
    user = state.get_user(msg.chat.id)
    
    print(user.registered)
    if user.registered: 
        bot.send_message(msg.chat.id, "You are already registered!")
        return None

    bot.send_message(msg.chat.id, "Please, Enter the password!")
    state.set_response_state(msg.chat.id, "reg_passwd_wait")

@bot.message_handler(commands=["login"])
def login(msg):
    state.add_user(msg.chat.id)
    user = state.get_user(msg.chat.id)

    if user.logged_in: 
        bot.send_message(msg.chat.id, "You are already logged in")
        return None
    
    bot.send_message(msg.chat.id, "Please, Enter the password!")
    state.set_response_state(msg.chat.id, "log_passwd_wait")

@bot.message_handler(commands=["predict"])
def predict(msg):
    state.add_user(msg.chat.id)
    user = state.get_user(msg.chat.id)
        
    status, m = state.check_auth(msg.chat.id)
    if not status:
        bot.send_message(msg.chat.id, m)
        return None
 
    bot.send_message(msg.chat.id, "Send me the image!")
    state.set_response_state(msg.chat.id, "waiting_image")
    
@bot.message_handler(content_types=['photo'], func=lambda msg: state.get_response_state(msg.chat.id) == "waiting_image")
def handle_prediction(msg):
    try:
        f_id = msg.photo[-1].file_id
        print(f_id)
        f_info = bot.get_file(f_id)
        print(f_info.file_path)
        f_downloaded = bot.download_file(f_info.file_path)

        f_ext = f_info.file_path.split('.')[-1] if '.' in f_info.file_path else 'jpg'
        print(f_ext)
        f_name = f"saved/image_{msg.message_id}.{f_ext}"    
        print(f_name)
        with open(f_name, "wb") as f:
            f.write(f_downloaded)

        prediction = state.predict(f_name)
        bot.send_message(msg.chat.id, prediction)
        # bot.send_message(msg.chat.id, "Image saved successfully!")
    except Exception as err:
        print(err)
        bot.send_message(msg.chat.id, "Something went wrong with image handling. Try another image.")
        
@bot.message_handler(func=lambda msg: state.get_response_state(msg.chat.id) == "reg_passwd_wait")
def handle_registration(msg):
    bot.send_message(msg.chat.id, "I have received you password! Now You are registered!")
    state.register(msg.chat.id, msg.text)
    state.set_response_state(msg.chat.id, "")

@bot.message_handler(func=lambda msg: state.get_response_state(msg.chat.id) == "log_passwd_wait")
def handle_signin(msg):
    res, m = state.login(msg.chat.id, msg.text)
    state.set_response_state(msg.chat.id, "")
    bot.send_message(msg.chat.id, m)


# Webhooks Section

app = Flask(__name__)

@app.post("/bot")
def webhooks():
    req = request.json
    update = Update.de_json(req)
    bot.process_new_updates([update])
    return "", 200

if __name__ == "__main__":
    app.run(host= '0.0.0.0',debug=True)
