import requests
import logging


class Telegram:
    def __init__(self, token, chat_id):
        self.token = token
        if isinstance(chat_id, list):
            self.chat_id = chat_id
        else:
            self.chat_id = list()
            self.chat_id.append(chat_id)
        self.url = 'https://api.telegram.org/bot{}'.format(self.token)
        self.parse_mode = '&parse_mode=HTML'

    def send_message(self, text):
        for _id in self.chat_id:
            send = self.url + '/sendMessage?chat_id=' + _id + self.parse_mode + '&text=' + text
            response = requests.get(send)
            if response.ok:
                logging.info('message to {} sent'.format(_id))
            else:
                logging.warning('message does not sent. response: {}'.format(response.text))
