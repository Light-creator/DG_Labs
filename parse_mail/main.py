import requests
import json
import argparse

from urllib.parse import unquote, quote, urlencode


class Mailer:
    def __init__(self, settings_file: str):
        self.session = requests.Session()
        self.settings_file = settings_file
        self.settings = None
        self.get_mail_by_id_postdata = None

        self.mails = None

        self.load_settings()
        self.load_headers()

    def load_settings(self) -> None:
        with open(self.settings_file, "r") as f:
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
        except JSONDecodeError as err:
            raise JSONDecodeError(f"Failed to parse mails")
    
    def print_mail(self, mail, extended_mail):
        print("-----------------------")
        print(f"Author: {mail['UniqueSenders']}")
        print(f"Topic: {mail['ConversationTopic']}")
        print(f"DateTime: {mail['LastDeliveryTime']}")
        if extended_mail == None: print(f"This mail does not have list of attachments")
        else: 
            print(f"List of attachments:")
            items = extended_mail['Body']['ResponseMessages']['Items']
            attachments = items[0]['Conversation']['ConversationNodes'][0]['Items'][0]['Attachments']
            for idx, attachment in enumerate(attachments):
                print(f"{idx}: {attachment['Name']} - {attachment['ContentType']}")
        print(f"Preview: {mail['Preview']}")
        print("-----------------------\n")
    
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
            return res_json
        except JSONDecodeError as err:
            print("Failed to load attachments!")
            return None


    def get_mails_with_author_filter(self, author: str) -> None:
        self.get_all_mails()

        for mail in self.mails["Body"]["Conversations"]:
            for sender in mail["UniqueSenders"]:
                if author in sender: 
                    extended_mail = None
                    if mail["HasAttachments"]: extended_mail = self.get_extended_mail(mail)
                    self.print_mail(mail, extended_mail)


def helper(args, mailer: Mailer) -> None:
    mailer.get_mails_with_author_filter(args.author)

def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("operation", type=str, help="Operation [send or get]")
    parser.add_argument("settings_file", type=str, help="File with settings (json format)")
    
    parser.add_argument("-t", "--topic", type=str, help="Filter for mail by topic")
    parser.add_argument("-d", "--date", type=str, help="Filter for mail by date")
    parser.add_argument("-a", "--author", type=str, help="Filter for mail by author")
    parser.add_argument("-b", "--body", type=str, help="Filter for mail by body text")
    
    args = parser.parse_args()

    mailer = Mailer(args.settings_file)
    
    helper(args, mailer)
    

if __name__ == "__main__":
    main()
