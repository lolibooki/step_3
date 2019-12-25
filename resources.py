from flask_restful import Resource, reqparse
from passlib.hash import pbkdf2_sha256 as sha256
from flask_jwt_extended import (create_access_token,
                                create_refresh_token,
                                jwt_required,
                                jwt_refresh_token_required,
                                get_jwt_identity,
                                get_raw_jwt)
# from userschema import validate_user
from bson.objectid import ObjectId
from suds.client import Client
import models
import datetime

# TODO: make settings file instead of below!
MMERCHANT_ID = 'aca6038e-06a7-11e9-bcad-005056a205be'  # TODO: replace with original merchant id
ZARINPAL_WEBSERVICE = 'https://www.zarinpal.com/pg/services/WebGate/wsdl'
PAYMENT_DESCRIPTION = 'بابت خرید دوره {}'
SERVER_IP = '136.243.32.187'
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
            return {'status': 400,
                    'message': 'User {} already exists'. format(data['mphone'])}

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
            return {'status': 500,
                    'message': 'Something went wrong'}


class UserLogin(Resource):
    def post(self):
        parser_copy = parser.copy()
        parser_copy.add_argument('mphone', help='This field cannot be blank', required=True)
        parser_copy.add_argument('pass', help='This field cannot be blank', required=True)
        data = parser_copy.parse_args()

        current_user = models.find_user({"mphone": data['mphone']})
        current_user["_id"] = str(current_user['_id'])
        if not current_user:
            return {'status': 400,
                    'message': 'User {} doesn\'t exist'.format(data['mphone'])}

        if sha256.verify(data['pass'], current_user['pass']):
            access_token = create_access_token(identity=data['mphone'])
            refresh_token = create_refresh_token(identity=data['mphone'])
            return {
                'status': 200,
                'message': 'Logged in as {}'.format(current_user['mphone']),
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user_data': {key: current_user.get(key, None) for key in ['fname',
                                                                 'lname',
                                                                 'mphone',
                                                                 'phone',
                                                                 'email',
                                                                 'mcode',
                                                                 'state',
                                                                 'city',
                                                                 'address']}
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
            return {'status': 200,
                    'message': 'Access token has been revoked'}
        except:
            return {'status': 500,
                    'message': 'Something went wrong'}


class UserLogoutRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = models.RevokedToken(jti)
            revoked_token.add()
            return {'status': 200,
                    'message': 'Access token has been revoked'}
        except:
            return {'status': 500,
                    'message': 'Something went wrong'}


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return {'status': 200,
                'access_token': access_token}


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


# TODO: check for user payment installments
class GetUserIPCourses(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        user = models.find_user({"mphone": current_user})
        courses = list()
        for item in user['ipcourse']:
            current_course = models.get_user_ip_course(item)
            current_course['_id'] = str(current_course['_id'])
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
            current_course['_id'] = str(current_course['_id'])
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
            current_course['_id'] = str(current_course['_id'])
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


class GetPayUrl(Resource):
    @jwt_required
    def post(self):
        parser_copy = parser.copy()
        parser_copy.add_argument('_id', help='This field cannot be blank', required=True)
        parser_copy.add_argument('ctype', help='This field cannot be blank', required=True)  # ip/rec/liv
        parser_copy.add_argument('method', help='This field cannot be blank', required=True)  # 1:full/3:installment
        data = parser_copy.parse_args()

        if data['ctype'] == "ip":
            courses = models.ip_courses(_id=data['_id'])
        elif data['ctype'] == "rec":
            courses = models.rec_courses(_id=data['_id'])
        elif data['ctype'] == "liv":
            courses = models.live_courses(_id=data['_id'])
        else:
            return {'status': 400,
                    'message': 'course type or id is incorrect'}
        try:
            course_price = int(courses['price'])/int(data['method'])
            payment_desc = PAYMENT_DESCRIPTION.format(courses['title'])
            # for item in courses:
            #     if item["_id"] == ObjectId(data['_id']):
            #         course_price = int(item['price'])/int(data['method'])
            #         payment_desc = PAYMENT_DESCRIPTION.format(item['title'])
            if not course_price or not payment_desc:
                return {'status': 500,
                        'message': 'course does not exist'}
        except KeyError as e:
            return {'status': 404,
                    'message': e}

        current_user = get_jwt_identity()
        user = models.find_user({'mphone': current_user})

        callback_url = SERVER_IP + '/PayCallback/{}/{}/{}/{}/{}'.format(data['method'],
                                                                        str(user['_id']),
                                                                        data['_id'],
                                                                        course_price,
                                                                        data['ctype'])

        client = Client(ZARINPAL_WEBSERVICE)
        result = client.service.PaymentRequest(MMERCHANT_ID,
                                               course_price,
                                               payment_desc,
                                               callback_url)
        if result.Status == 100:
            return {'status': 200,
                    'url': 'https://www.zarinpal.com/pg/StartPay/' + result.Authority}
        else:
            return {'status': 500,
                    'error': 'Zarinpal not responding'}
