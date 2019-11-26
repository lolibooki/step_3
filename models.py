from run import mongo


def create_user(new_user):
    mongo.db.users.insert_one(new_user)


def find_one(key):
    return mongo.db.users.find_one(key)


def live_classes():
    lives = [item for item in mongo.db.lives.find()]  # return list of live classes
    for it in lives:
        it["_id"] = str(it["_id"])
    return lives


def ip_courses():
    ips = [item for item in mongo.db.ip.find()]  # return list of in person courses
    for it in ips:
        it["_id"] = str(it["_id"])
    return ips


def rec_courses():
    recs = [item for item in mongo.db.rec.find()]  # return list of recorded courses
    for it in recs:
        it["_id"] = str(it["_id"])
    return recs


def live_courses():
    lives = [item for item in mongo.db.livc.find()]  # return list of live courses
    for it in lives:
        it["_id"] = str(it["_id"])
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
