from run import mongo

def create_user(new_user):
    mongo.db.users.insert_one(new_user)

def find_one(key):
    return mongo.db.users.find_one(key)