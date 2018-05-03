import datetime

import argon2
from flask_login import UserMixin
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer,
                          BadSignature, SignatureExpired)
import peewee as pw

import config


DATABASE = pw.SqliteDatabase('todos.sqlite')
HASHER = argon2.PasswordHasher()


class User(UserMixin, pw.Model):
    username = pw.CharField(unique=True)
    password = pw.CharField(max_length=64)

    class Meta:
        database = DATABASE

    @classmethod
    def create_user(cls, username, password):
        """Create user with hashed password"""
        try:
            cls.select().where(cls.username**username).get()
        except cls.DoesNotExist:
            user = cls(username=username)
            user.password = user.set_password(password)
            user.save()
            return user
        else:
            raise Exception("User with that username already exists")

    @staticmethod
    def verify_auth_token(token):
        serializer = Serializer(config.SECRET_KEY)
        try:
            data = serializer.loads(token)
        except (SignatureExpired, BadSignature):
            return None
        else:
            user = User.get(User.id == data['id'])
            return user

    def generate_auth_token(self, expires=3600):
        serializer = Serializer(config.SECRET_KEY, expires_in=expires)
        return serializer.dumps({'id': self.id})

    @staticmethod
    def set_password(password):
        return HASHER.hash(password)

    def verify_password(self, password):
        return HASHER.verify(self.password, password)


class Todo(pw.Model):
    name = pw.CharField()
    completed = pw.BooleanField(default=False)
    created_date = pw.DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = DATABASE
        order_by = ('created_date',)


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Todo], safe=True)
    DATABASE.close()
