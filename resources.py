from flask_restful import Resource, reqparse
from passlib.hash import pbkdf2_sha256 as sha256
from flask_jwt_extended import (create_access_token,
                                create_refresh_token,
                                jwt_required,
                                jwt_refresh_token_required,
                                get_jwt_identity,
                                get_raw_jwt)
# from userschema import validate_user
import models
from bson.objectid import ObjectId
import datetime

parser = reqparse.RequestParser()
# parser.add_argument('fname', help = 'This field cannot be blank', required = True)
# parser.add_argument('password', help = 'This field cannot be blank', required = True)


class UserRegistration(Resource):
    def post(self):

        parser_copy = parser.copy()
        # required
        parser_copy.add_argument('fname', help='This field cannot be blank', required=True)
        parser_copy.add_argument('lname', help='This field cannot be blank', required=True)
        parser_copy.add_argument('mphone', help='This field cannot be blank', required=True)
        parser_copy.add_argument('email', help='This field cannot be blank', required=True)
        parser_copy.add_argument('mcode', help='This field cannot be blank', required=True)
        parser_copy.add_argument('pass', help='This field cannot be blank', required=True)
        # not required
        parser_copy.add_argument('phone', required=False)
        parser_copy.add_argument('state', required=False)
        parser_copy.add_argument('city', required=False)
        parser_copy.add_argument('address', required=False)

        data = parser_copy.parse_args()

        if models.find_user({"mphone": data['mphone']}):  # check if user is new or not
            return {'message': 'User {} already exists'. format(data['mphone'])}

        new_user = {
            "fname": data['fname'],
            "lname": data['lname'],
            "mphone": data['mphone'],
            "phone": data['phone'],
            "email": data['email'],
            "mcode": data['mcode'],
            "state": data['state'],
            "city": data['city'],
            "address": data['address'],
            "pass": sha256.hash(data['pass']),
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
        parser_copy = parser.copy()
        parser_copy.add_argument('mphone', help='This field cannot be blank', required=True)
        parser_copy.add_argument('pass', help='This field cannot be blank', required=True)
        data = parser_copy.parse_args()

        current_user = models.find_user({"mphone": data['mphone']})
        if not current_user:
            return {'message': 'User {} doesn\'t exist'.format(data['mphone'])}

        if sha256.verify(data['pass'], current_user['pass']):
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


class Test(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        return current_user


class GetUserIPCourses(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        user = models.find_user({"mphone": current_user})
        courses = list()
        for item in user['ipcourse']:
            current_course = models.get_user_ip_course(item)
            current_course['_id'] = str(current_course['id'])
            courses.append(current_course)
        return courses


class GetUserLiveCourses(Resource):  # TODO: checking users absences
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        user = models.find_user({"mphone": current_user})
        live_course_ids = list(user['livecourse'].keys())
        courses = list()
        for item in live_course_ids:
            current_course = models.get_user_live_course(item)
            current_course['_id'] = str(current_course['id'])
            courses.append(current_course)
        return courses


# checking for course weeks and does not allow that future weeks include in response json
class GetUserRecCourses(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        user = models.find_user({'mphone': current_user})
        rec_course_ids = list(user['reccourse'].keys())
        current_date = datetime.datetime.now()
        current_time = datetime.date(current_date.year, current_date.month, current_date.day).isocalendar()
        courses = list()
        for item in rec_course_ids:
            current_course = models.get_user_rec_course(item)
            current_course['_id'] = str(current_course['id'])
            course_time = datetime.date(current_course['s_time'].year,
                                        current_course['s_time'].month,
                                        current_course['s_time'].day).isocalendar()
            if current_time[0] == course_time[0]:
                week_delta = current_time[1] - course_time[1]
            else:
                week_delta = current_time[1] + 52 - course_time[1]
            for week in current_course['weeks']:
                if int(week) > week_delta:
                    current_course['weeks'][week] = None
            courses.append(current_course)
        return courses

