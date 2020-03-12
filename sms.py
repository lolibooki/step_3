from ippanel import Client, Error


class Sms:
    def __init__(self):
        self.phone = "+9810009589"
        self.api_key = "w-_o3HD2Uz5D-UtibVcGj4q5R4_POJhpVeXrZC2NjZE="
        self.pattern_code = "e06081mqm5"
        self.client = Client(self.api_key)
        
        
    def send_code(self, verify_code, recipient_number):
        pattern_val = {'verify': str(verify_code)}
        try:
            resp = self.client.send_pattern(self.pattern_code,
                                            self.phone,
                                            recipient_number,
                                            pattern_val)
            return True, resp
        except Error as e:
            return ('error: {}'.format(e))
        