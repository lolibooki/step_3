from flask_restful import Resource, reqparse
from passlib.hash import pbkdf2_sha256 as sha256
from flask_jwt_extended import (create_access_token,
                                create_refresh_token,
                                jwt_required,
                                jwt_refresh_token_required,
                                get_jwt_identity,
                                get_raw_jwt)
from userschema import validate_user
import models

parser = reqparse.RequestParser()
# parser.add_argument('username', help = 'This field cannot be blank', required = True)
# parser.add_argument('password', help = 'This field cannot be blank', required = True)


class UserRegistration(Resource):
    def post(self):
        if validate_user(parser.parse_args()):  # check if incoming data is correct
            data = parser.parse_args()
        else:
            return validate_user(parser.parse_args())

        if models.find_one({"mphone": data['mphone']}):  # check if user is new or not
            return {'message': 'User {} already exists'. format(data['username'])}

        new_user = {
            "fname": data['fname'],
            "lname": data['lname'],
            "mphone": data['mphone'],
            "phone": data['phone'] if data['phone'] in data.keys() else None,
            "email": data['email'],
            "mcode": data['mcode'],
            "state": data['state'] if data['state'] in data.keys() else None,
            "city": data['city'] if data['city'] in data.keys() else None,
            "address": data['address'] if data['address'] in data.keys() else None,
            "pass": sha256.hash(data['password']),
        }

        try:
            models.create_user(new_user)
            access_token = create_access_token(identity=data['mphone'])
            refresh_token = create_refresh_token(identity=data['mphone'])
            return {
                'message': 'User {} {} was created'.format(data['fname'], data['lname']),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogin(Resource):
    def post(self):
        data = parser.parse_args()
        current_user = models.find_one({"mphone": data['mphone']})
        if not current_user:
            return {'message': 'User {} doesn\'t exist'.format(data['mphone'])}
        
        if sha256.verify(data['password'], current_user['password']):
            access_token = create_access_token(identity=data['mphone'])
            refresh_token = create_refresh_token(identity=data['mphone'])
            return {
                'message': 'Logged in as {}'.format(current_user['mphone']),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        else:
            return {'message': 'Wrong credentials'}


class UserLogoutAccess(Resource):
    @jwt_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = models.RevokedToken(jti)
            revoked_token.add()
            return {'message': 'Access token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogoutRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = models.RevokedToken(jti)
            revoked_token.add()
            return {'message': 'Access token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return {'access_token': access_token}


class GetLiveClasses(Resource):
    def get(self):
        return models.live_classes()


class GetRecordedCourses(Resource):
    def get(self):
        return models.rec_courses()


class GetLiveCourses(Resource):
    def get(self):
        return models.live_courses()


class GetInPersonCourses(Resource):
    def get(self):
        return models.ip_courses()
