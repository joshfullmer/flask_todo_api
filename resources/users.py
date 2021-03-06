from flask import Blueprint
from flask_restful import Resource, Api, reqparse, fields, marshal

from auth import auth
import models

user_fields = {
    'username': fields.String,
}


class UserList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'username',
            required=True,
            help='no username provided',
            location=['form', 'json']
        )
        self.reqparse.add_argument(
            'password',
            required=True,
            help='no password provided',
            location=['form', 'json']
        )
        self.reqparse.add_argument(
            'verify_password',
            required=True,
            help='no password verification provided',
            location=['form', 'json']
        )
        super().__init__()

    @auth.login_required
    def post(self):
        args = self.reqparse.parse_args()
        if args['password'] == args['verify_password']:
            user = models.User.create_user(
                username=args.get('username'),
                password=args.get('password'))
            return marshal(user, user_fields), 201
        return ({'error': 'Password and password verification do not match'},
                400)


users_api = Blueprint('resources.users', __name__)
api = Api(users_api)
api.add_resource(
    UserList,
    '/users',
    endpoint='users'
)
