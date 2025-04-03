import requests
import json
import argparse

from urllib.parse import unquote, quote_plus


class Mailer:
    def __init__(self, settings_file: str):
        self.session = requests.Session()
        self.settings_file = settings_file
        self.settings = None
        self.get_mail_by_id_postdata = None

        self.mails = None

        self.load_settings()
        self.load_headers()

    def load_settings(self):
        with open(self.settings_file, "r") as f:
            self.settings = json.load(f, strict=False)

    def load_headers(self):
        postdata = unquote(self.settings["headers"]["get_conversation_by_id"]["X-Owa-Urlpostdata"]) 
        self.get_mail_by_id_postdata = json.loads(postdata)
        
    def get_all_mails(self):
        self.session.headers.clear()
        self.session.headers.update(self.settings["session"])
        self.session.headers.update(self.settings["headers"]["get_conversations"])

        res = self.session.get(self.settings["urls"]["get_conversations"])
        self.mails = json.loads(res.text)
    
    def get_mail_by_id(self, id: str):
        self.get_mail_by_id_postdata["Body"]["Conversations"]["ConversationId"]["Id"] = id
        
        self.session.headers.clear()
        self.session.headers.update(self.settings["session"])
        self.session.headers.update({"X-Owa-Urlpostdata": quote_plus(self.get_mail_by_id_postdata), "Action": "GetConversationItems"})

        res = self.session.get(self.settings["urls"]["get_conversation_by_id"])

    def get_full_mails_by_author(self, autor: str):
        for mail in self.mails:
            if author in mail["UniqueRecipients"]:
                get_mail_by_id(mail["ConversationId"]["Id"])
        

def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("operation", type=str, help="Operation [send or get]")
    parser.add_argument("settings_file", type=str, help="File with settings (json format)")
    
    parser.add_argument("-t", "--topic", type=str, help="Filter for mail by topic")
    parser.add_argument("-d", "--date", type=str, help="Filter for mail by date")
    parser.add_argument("-a", "--autor", type=str, help="Filter for mail by author")
    parser.add_argument("-b", "--body", type=str, help="Filter for mail by body text")
    
    args = parser.parse_args()

    mailer = Mailer(args.settings_file)

    
    

if __name__ == "__main__":
    main()
