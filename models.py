from run import mongo

def create_user(new_user):
    mongo.db.users.insert_one(new_user)

def find_one(key):
    return mongo.db.users.find_one(key)

def live_classes():
    lives = [item for item in mongo.db.lives.find({}, {'_id': False})]
    return lives

class RevokedToken:
    def __init__(self, jti):
        self.query = {'jti': jti}
    
    def add(self):
        mongo.db.bjti.insert_one(self.query)
    
    @staticmethod
    def is_jti_blacklisted(jti):
        query = mongo.db.bjti.find_one(jti)
        if query:
            return True
        return False
