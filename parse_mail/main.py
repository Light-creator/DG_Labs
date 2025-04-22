import requests
import json
import argparse

from datetime import datetime
from urllib.parse import unquote, quote, urlencode


class Mailer:
    def __init__(self, settings_file: str):
        self.session = requests.Session()
        self.settings_file = settings_file
        self.settings = None
        self.get_mail_by_id_postdata = None

        self.mails = None
        self.extended_mails = None

        self.load_settings()
        self.load_headers()

    def load_settings(self) -> None:
        with open(self.settings_file, "r", encoding="utf-8") as f:
            self.settings = json.load(f, strict=False)

    def load_headers(self) -> None:
        postdata = unquote(self.settings["headers"]["get_conversation_by_id"]["X-Owa-Urlpostdata"]) 
        self.get_mail_by_id_postdata = json.loads(postdata)
        
    def get_all_mails(self) -> None:
        try:
            self.session.headers.clear()
            self.session.headers.update(self.settings["session"])
            self.session.headers.update(self.settings["headers"]["get_conversations"])

            res = self.session.post(self.settings["urls"]["get_conversations"])
            self.mails = json.loads(res.text)
        except Exception as err:
            raise Exception(f"Failed to parse mails", err)
    
    def print_mail(self, mail, extended_mail):
        try:
            print("-----------------------")
            print(f"Author: {mail['UniqueSenders']}")
            print(f"Topic: {mail['ConversationTopic']}")
            print(f"DateTime: {mail['LastDeliveryTime']}")
            if not mail["HasAttachments"] or extended_mail == None: 
                print(f"This mail does not have list of attachments")
            else: 
                print(f"List of attachments:")
                attachments = extended_mail['Attachments']
                for idx, attachment in enumerate(attachments):
                    print(f"    {idx+1}: {attachment['Name']} - {attachment['ContentType']}")
            print(f"Preview: {mail['Preview']}")
            print("-----------------------\n")
        except:
            # Failed to print mail
            return None
    
    def get_extended_mail(self, mail):
        try:
            self.session.headers.clear()
            self.session.headers.update(self.settings["session"])
        
            post_data = self.settings["post_req_conversation_by_id"]
            post_data["Body"]["Conversations"][0]["ConversationId"]["Id"] = mail["ConversationId"]["Id"]
            self.session.headers.update({"X-Owa-Urlpostdata": quote(json.dumps(post_data))})
            self.session.headers.update({"Action": "GetConversationItems"})

            res = self.session.post(self.settings["urls"]["get_conversation_by_id"])
            res_json = json.loads(res.text)
            items = res_json['Body']['ResponseMessages']['Items']
            res_mail = items[0]['Conversation']['ConversationNodes'][0]['Items'][0]
            return res_mail
        except Exception as err:
            print("Failed to load attachments!")
            return None
    
    def is_filtered(self, args, mail, extended_mail=None) -> bool:
        try:
            if args.author != None: 
                for sender in mail["UniqueSenders"]:
                    if args.author in sender: return True
            elif args.topic != None: return args.topic in mail["ConversationTopic"]
            elif args.date != None:
                date = datetime.strptime(mail["LastDeliveryTime"], "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
                filter_date = datetime.strptime(args.date, "%d.%m.%Y")
                if date.date() == filter_date.date(): return True
            elif args.body != None:
                if extended_mail != None: return args.body in extended_mail["UniqueBody"]["Value"]
                else: return args.body in mail["Preview"]
            return False
        except:
            return False

    def get_mails_with_filter(self, args) -> None:
        self.get_all_mails()

        for mail in self.mails["Body"]["Conversations"]:
            extended_mail = None
            if args.body != None or mail["HasAttachments"]:
                extended_mail = self.get_extended_mail(mail)
            if self.is_filtered(args, mail, extended_mail): 
                self.print_mail(mail, extended_mail)

    def send_mail(self, args):
        try:
            self.session.headers.clear()
            self.session.headers.update(self.settings["session"])
            self.session.headers.update({"Action": "CreateItem"})
        
            post_data = self.settings["post_send_mail"]
            
            post_data["Body"]["Items"][0]["ToRecipients"] = []
            for receiver in args.receivers.split(','):
                post_data["Body"]["Items"][0]["ToRecipients"] += [{
                  "__type": "EmailAddress:#Exchange",
                  "EmailAddress": receiver,
                  "Name": receiver,
                  "RoutingType": "SMTP",
                  "MailboxType": "OneOff"
                }]

            post_data["Body"]["Items"][0]["Subject"] = args.topic
            post_data["Body"]["Items"][0]["Body"]["Value"] = f"</p>{args.body}</p>"
            
            res = self.session.post(self.settings["urls"]["send_mail"], json=post_data)
            # print(f"{res} {res.text}")
        except Exception as err:
            raise Exception("Failed to send mail", err)


def helper(args, mailer: Mailer) -> None:
    if args.operation == "get":
        mailer.get_mails_with_filter(args)
    elif args.operation == "send":
        mailer.send_mail(args)
    else:
        raise Exception(f"Unknown operation {args.operation}")

def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("operation", type=str, help="Operation [send or get]")
    parser.add_argument("settings_file", type=str, help="File with settings (json format)")
    
    parser.add_argument("-t", "--topic", type=str, help="Filter for mail by topic")
    parser.add_argument("-d", "--date", type=str, help="Filter for mail by date [dd.mm.yyyy]")
    parser.add_argument("-a", "--author", type=str, help="Filter for mail by author")
    parser.add_argument("-b", "--body", type=str, help="Filter for mail by body text")
    parser.add_argument("-r", "--receivers", type=str, help="List of Receivers")
    
    args = parser.parse_args()

    mailer = Mailer(args.settings_file)


    if args.operation == "get" and not args.topic and not args.author and not args.body and not args.date:
        raise Exception("Filter parameter should be not None for get operation")
    if args.operation == "send":
        if not args.body:
            raise Exception("Body argument is required")
        if not args.receivers:
            raise Exception("Receivers argument is required")
        if not args.topic:
            raise Exception("Topic argument is required")
    
    helper(args, mailer)
    

if __name__ == "__main__":
    main()
