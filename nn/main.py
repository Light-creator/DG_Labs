import telebot

token = '7842649076:AAGplncQ6y17P3X2ojk_Sl_1v7qjT3KL-EE'

class Client:
    def __init__(self):
        self.logged_in = False
        self.registered = False
        self.passwd = None
        self.chat_id = None

        self.response_state = ""

class State:
    def __init__(self):
        self.db = {}

    def restart(self):
        self.db = {}
    
    def register(self, chat_id, passwd) -> (bool, str):
        if chat_id in self.db and self.db[chat_id].registered:
            return False, "You are already registered!"

        self.db[chat_id].registered = True
        self.db[chat_id].passwd = passwd

    def add_client(self, chat_id):
        if chat_id in self.db: return None

        self.db[chat_id] = Client()

    def login(self, chat_id, passwd) -> (bool, str):
        if chat_id not in self.db:
            return False, "You are not registered yet!"
        
        if self.db[chat_id].logged_in:
            return True, "You are already logged in!"

        if self.db[chat_id].passwd != passwd:
            return False, "Incorrect password!"
        
        self.db[chat_id].logged_in = True
        return True, "You successfully logged in!"

    def get_response_state(self, chat_id) -> str:
        if chat_id in self.db: 
            return self.db[chat_id].response_state

        return ""

    def set_response_state(self, chat_id, resp_state):
        self.db[chat_id].response_state = resp_state
    
    def check_registration(self, chat_id) -> (bool, str):
        if chat_id in self.db and self.db[chat_id].registered:
            return True, "You are already registered!"

        return False, "You are not registered yet!"


    def check_auth(self, chat_id) -> (bool, str):
        if self.db[chat_id].logged_in:
            return True, "You are logged in!"

        return False, "You are not logged in!"


bot = telebot.TeleBot(token)

state = State()

@bot.message_handler(commands=["build"])
def restart_bot(msg):
    state.restart()

@bot.message_handler(commands=["start"])
def start_message(msg):
    state.add_client(msg.chat.id)
    bot.send_message(msg.chat.id, "Hello, Welcome!")

@bot.message_handler(commands=["register"])
def register(msg):
    is_reg, m = state.check_registration(msg.chat.id)
    
    if is_reg: 
        bot.send_message(msg.chat.id, m)
        return None

    bot.send_message(msg.chat.id, "Please, Enter the password!")
    state.set_response_state(msg.chat.id, "reg_passwd_wait")

@bot.message_handler(commands=["login"])
def login(msg):
    is_logged_in, m = state.check_auth()
    
    if not is_logged_in: 
        bot.send_message(msg.chat.id, m)
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
