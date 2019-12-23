from flask import Flask, jsonify, request
from flask_restful import Api
# from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from bson.objectid import ObjectId
from suds.client import Client
import datetime

MMERCHANT_ID = 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'  # TODO: replace with original merchant id
ZARINPAL_WEBSERVICE = 'https://www.zarinpal.com/pg/services/WebGate/wsdl'

app = Flask(__name__)
api = Api(app)

app.config["MONGO_URI"] = "mongodb://localhost:27017/students"
app.config['SECRET_KEY'] = 'some-secret-string'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

jwt = JWTManager(app)
mongo = PyMongo(app)


@app.route('/')
def index():
    return jsonify({'message': 'Hello, World!'})


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return models.RevokedToken.is_jti_blacklisted({"jti": jti})


@app.route('/PayCallback/<int:method>/<str:user>/<str:course/<int:price>', methods=['GET', 'POST'])
def verify(method, user, course, price):
    client = Client(ZARINPAL_WEBSERVICE)
    if request.args.get('Status') == 'OK':
        result = client.service.PaymentVerification(MMERCHANT_ID,
                                                    request.args['Authority'],
                                                    price)
        if result.Status == 100:
            return 'Transaction success. RefID: ' + str(result.RefID)
        elif result.Status == 101:
            return 'Transaction submitted : ' + str(result.Status)
        else:
            return 'Transaction failed. Status: ' + str(result.Status)
    else:
        return 'Transaction failed or canceled by user'

import models, resources

api.add_resource(resources.UserRegistration, '/registration')
api.add_resource(resources.UserLogin, '/login')
api.add_resource(resources.UserLogoutAccess, '/logout/access')
api.add_resource(resources.UserLogoutRefresh, '/logout/refresh')
api.add_resource(resources.TokenRefresh, '/token/refresh')
api.add_resource(resources.GetLiveClasses, '/liveClass')
api.add_resource(resources.GetRecordedCourses, '/recCourse')
api.add_resource(resources.GetLiveCourses, '/liveCourse')
api.add_resource(resources.GetInPersonCourses, '/inpersonCourse')
api.add_resource(resources.GetUserIPCourses, '/userIPCourse')
api.add_resource(resources.GetUserLiveCourses, '/userLiveCourse')
api.add_resource(resources.GetUserRecCourses, '/userRecCourse')
api.add_resource(resources.GetPayUrl, '/pay/getUrl')
api.add_resource(resources.Test, '/test')


if __name__ == "__main__":
    app.run()
