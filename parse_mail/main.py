import requests
import json
import parseargs


class Mailer:
    def __init__(self, session_file):
        self.session = requests.Session()
        
        self.session_file = session_file 

        self.session_cookies = None
        self.mails_headers = None
        self.mails = None

        self.get_session_cookies()
        self.get_mail_headers()
        
    def get_session_cookies(self) -> None:
        try:
            f = open(self.session_file, "r")
            cookies = f.read().strip()
            headers = {
                    "Cookie": cookies
                    }

            f.close()
            self.session_cookies = {"Cookie": cookies}
       except FileNotFoundError:
           raise FileNotFoundError(f"file {self.session_file} not found")
    
    def get_mail_headers(self) -> None:
        self.mails_headers = {"X-Owa-Urlpostdata": "%7B%22__type%22%3A%22FindConversationJsonRequest%3A%23Exchange%22%2C%22Header%22%3A%7B%22__type%22%3A%22JsonRequestHeaders%3A%23Exchange%22%2C%22RequestServerVersion%22%3A%22V2016_02_03%22%2C%22TimeZoneContext%22%3A%7B%22__type%22%3A%22TimeZoneContext%3A%23Exchange%22%2C%22TimeZoneDefinition%22%3A%7B%22__type%22%3A%22TimeZoneDefinitionType%3A%23Exchange%22%2C%22Id%22%3A%22Russian%20Standard%20Time%22%7D%7D%7D%2C%22Body%22%3A%7B%22__type%22%3A%22FindConversationRequest%3A%23Exchange%22%2C%22ParentFolderId%22%3A%7B%22__type%22%3A%22TargetFolderId%3A%23Exchange%22%2C%22BaseFolderId%22%3A%7B%22__type%22%3A%22DistinguishedFolderId%3A%23Exchange%22%2C%22Id%22%3A%22inbox%22%7D%7D%2C%22ConversationShape%22%3A%7B%22__type%22%3A%22ConversationResponseShape%3A%23Exchange%22%2C%22BaseShape%22%3A%22IdOnly%22%7D%2C%22ShapeName%22%3A%22ConversationListView%22%2C%22Paging%22%3A%7B%22__type%22%3A%22IndexedPageView%3A%23Exchange%22%2C%22BasePoint%22%3A%22Beginning%22%2C%22Offset%22%3A0%2C%22MaxEntriesReturned%22%3A500%7D%2C%22ViewFilter%22%3A%22All%22%2C%22FocusedViewFilter%22%3A-1%2C%22SortOrder%22%3A%5B%7B%22__type%22%3A%22SortResults%3A%23Exchange%22%2C%22Order%22%3A%22Descending%22%2C%22Path%22%3A%7B%22__type%22%3A%22PropertyUri%3A%23Exchange%22%2C%22FieldURI%22%3A%22ConversationLastDeliveryOrRenewTime%22%7D%7D%2C%7B%22__type%22%3A%22SortResults%3A%23Exchange%22%2C%22Order%22%3A%22Descending%22%2C%22Path%22%3A%7B%22__type%22%3A%22PropertyUri%3A%23Exchange%22%2C%22FieldURI%22%3A%22ConversationLastDeliveryTime%22%7D%7D%5D%7D%7D", "Action": "FindConversation"}

    def set_headers_for_conversations_req(self) -> None:
        s.headers.clear()
        s.headers.update(self.session_cookies)
        s.headers.update(self.mail_headers)

    def get_all_mails(self) -> None:
        self.set_headers_for_conversations_req()
        res = self.session.get("https://mail.spbstu.ru/owa/service.svc?action=FindConversation")
        self.mails = json.loads(res.text)

    def filter_mails_by(self, filter_name: str, filter_value: str) -> None:
        pass

    def send_mail(self, topic: str, body: str) -> None:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("operation", type=str, help="Operation [send or get]")
    parser.add_argument("session_file", type=str, help="File with session creds")
    
    parser.add_argument("-t", "--topic", type=str, help="Filter for mail by topic")
    parser.add_argument("-d", "--date", type=str, help="Filter for mail by date")
    parser.add_argument("-a", "--autor", type=str, help="Filter for mail by author")
    parser.add_argument("-b", "--body", type=str, help="Filter for mail by body text")
    
    

    mailer = Mailer("session.txt")

    
    

if __name__ == "__main__":
    main()
