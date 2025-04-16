import telebot
import sqlite3
import time
import base64
from passlib.hash import bcrypt

token = '7842649076:AAGplncQ6y17P3X2ojk_Sl_1v7qjT3KL-EE'
db_name = 'data.db'

class Client:
    def __init__(self, user_tuple):
        self.id = user_tuple[0]
        self.logged_in = user_tuple[5]
        self.registered = user_tuple[4]
        self.passwd = user_tuple[2]
        self.chat_id = user_tuple[1]

        self.response_state = user_tuple[3]

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

    def update_registered(self, chat_id, session_id):
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
        
        session_id = self.session_id(chat_id)
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
    
    def session_expired(self, user):
        decoded_bytes = base64.b64decode(encoded)
        epoch_time = int(decoded_bytes.decode('utf-8'))
        dt = datetime.datetime.fromtimestamp(epoch_time)
        
        now = datetime.now()
        if now - datetime.timedelta(hours=1) > dt:
            return True

        return False

    def check_auth(self, chat_id) -> (bool, str):
        user = self.get_user(chat_id)
        
        if not user.logged_in:
            return False, "You are not logged in!"
        
        if self.session_expired(user):
            return False, "Your session has expired. Please, log in again!"

        return True, "You are logged in!"


bot = telebot.TeleBot(token)

state = State()

@bot.message_handler(commands=["start"])
def start_message(msg):
    state.add_user(msg.chat.id)
    user = state.get_user(msg.chat.id)
    print(user.passwd)
    bot.send_message(msg.chat.id, "Hello, Welcome!")

@bot.message_handler(commands=["register"])
def register(msg):
    state.add_user(msg.chat.id)
    user = state.get_user(msg.chat.id)

    if user.registered: 
        bot.send_message(msg.chat.id, "You are already registered!")
        return None

    bot.send_message(msg.chat.id, "Please, Enter the password!")
    state.set_response_state(msg.chat.id, "reg_passwd_wait")

@bot.message_handler(commands=["login"])
def login(msg):
    state.add_user(msg.chat.id)
    user = state.get_user()

    if user.logged_in: 
        bot.send_message(msg.chat.id, "You are already logged in")
        return None
    
    bot.send_message(msg.chat.id, "Please, Enter the password!")
    state.set_response_state(msg.chat.id, "log_passwd_wait")

    
@bot.message_handler(func=lambda msg: state.get_response_state(msg.chat.id) == "reg_passwd_wait")
def handle_registration(msg):
    bot.send_message(msg.chat.id, "I have received you password! Now You are registered!")
    state.register(msg.chat.id, msg.text)
    state.set_response_state(msg.chat.id, "")

@bot.message_handler(func=lambda msg: state.get_response_state(msg.chat.id) == "log_passwd_wait")
def handle_signin(msg):
    res, m = state.login(msg.chat.id, msg.text)
    state.set_response_state(msg.chat.id, "")
    bot.send_message(msg.chat_id, m)

bot.infinity_polling()
