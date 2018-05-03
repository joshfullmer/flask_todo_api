import base64
import json
import unittest

import peewee as pw

import app
from models import User, Todo


BASIC_AUTH_HEADERS = {'Authorization': 'Basic ' +
                      base64.b64encode(b'username:password').decode('ascii')}

MODELS = [Todo, User]

test_db = pw.SqliteDatabase(':memory:')


class BaseTest(unittest.TestCase):
    def setUp(self):
        for model in MODELS:
            model.bind(test_db, bind_refs=False, bind_backrefs=False)

        test_db.connect()
        test_db.create_tables(MODELS)

        app.app.config['TESTING'] = True
        app.app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.app.test_client()

    def tearDown(self):
        test_db.drop_tables(MODELS)
        test_db.close()


class SiteTest(BaseTest):
    def test_site(self):
        r = self.app.get('/')
        self.assertEqual(r.status_code, 200)


class DatabaseTest(BaseTest):
    def test_create_todo(self):
        Todo.create(name="First Test Todo")
        self.assertEqual(Todo.select().count(), 1)

    def test_create_user(self):
        User.create_user(username='username', password='password')
        self.assertEqual(User.select().count(), 1)

    def test_dupe_user_check(self):
        User.create_user(username='username', password='password')
        with self.assertRaises(Exception):
            User.create_user(username='username', password='password')


class UserTest(BaseTest):
    def test_login_page(self):
        r = self.app.get('/login')
        self.assertEqual(r.status_code, 200)

    def test_login_form(self):
        User.create_user(username='username', password='password')
        form = {'username': 'username', 'password': 'password'}
        r = self.app.post('/login', data=form)
        self.assertEqual(r.status_code, 302)

    def test_login_form_reject(self):
        User.create_user(username='username', password='password')
        form = {'username': 'username', 'password': 'drowssap'}
        r = self.app.post('/login', data=form)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Sign in failed.', r.data.decode())

    def test_login_user_missing(self):
        form = {'username': 'username', 'password': 'password'}
        r = self.app.post('/login', data=form)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Sign in failed.', r.data.decode())

    def test_signup_page(self):
        r = self.app.get('/signup')
        self.assertEqual(r.status_code, 200)

    def test_signup_form(self):
        form = {'username': 'username',
                'password': 'password',
                'password2': 'password'}
        r = self.app.post('/signup', data=form)
        self.assertEqual(r.status_code, 302)

    def test_signup_form_reject(self):
        form = {'username': 'username',
                'password': 'password',
                'password2': 'drowssap'}
        r = self.app.post('/signup', data=form)
        self.assertEqual(r.status_code, 200)
        self.assertIn('password must match', r.data.decode())

    def test_logout(self):
        user = User.create_user(username='username', password='password')
        with self.app as c:
            with c.session_transaction() as sess:
                sess['user_id'] = user.id
                sess['_fresh'] = True
            r = c.get('/logout')
            self.assertEqual(r.status_code, 302)


class APITest(BaseTest):

    def test_todo_list_get(self):
        Todo.create(name='Test Todo', completed=False)
        r = self.app.get('/api/v1/todos')
        r_dec = r.data.decode('utf-8')
        r_dec = json.loads(r_dec)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r_dec), 1)

    def test_todo_list_post(self):
        User.create_user(username='username', password='password')
        data = {'name': 'Test Todo', 'completed': False}
        r = self.app.post(
            '/api/v1/todos',
            data=data,
            headers=BASIC_AUTH_HEADERS,
            follow_redirects=True)
        self.assertEqual(r.status_code, 201)

    def test_todo_list_post_reject(self):
        data = {'name': 'Test Todo', 'completed': False}
        r = self.app.post('/api/v1/todos', data=data)
        self.assertEqual(r.status_code, 401)

    def test_todo_list_post_token(self):
        user = User.create_user(username='username', password='password')
        data = {'name': 'Test Todo', 'completed': False}
        token = user.generate_auth_token().decode('ascii')
        headers = {'Authorization': f'Token {token}'}
        r = self.app.post('/api/v1/todos', data=data, headers=headers)
        self.assertEqual(r.status_code, 201)

    def test_todo_put(self):
        User.create_user(username='username', password='password')
        todo = Todo.create(name='Test Todo', completed=False)
        r = self.app.put(
            f'/api/v1/todos/{todo.id}',
            data={'name': 'Test Todo', 'completed': True},
            headers=BASIC_AUTH_HEADERS)
        self.assertEqual(r.status_code, 200)

    def test_todo_put_reject(self):
        todo = Todo.create(name='Test Todo', completed=False)
        r = self.app.put(
            f'/api/v1/todos/{todo.id}',
            data={'name': 'Test Todo', 'completed': True},
            headers=BASIC_AUTH_HEADERS)
        self.assertEqual(r.status_code, 401)

    def test_todo_put_token(self):
        user = User.create_user(username='username', password='password')
        todo = Todo.create(name='Test Todo', completed=False)
        token = user.generate_auth_token().decode('ascii')
        headers = {'Authorization': f'Token {token}'}
        r = self.app.put(
            f'/api/v1/todos/{todo.id}',
            data={'name': 'Test Todo', 'completed': 'False'},
            headers=headers)
        self.assertEqual(r.status_code, 200)

    def test_todo_not_found(self):
        user = User.create_user(username='username', password='password')
        token = user.generate_auth_token().decode('ascii')
        headers = {'Authorization': f'Token {token}'}
        r = self.app.put(
            f'/api/v1/todos/{1}',
            data={'name': 'Test Todo', 'completed': 'False'},
            headers=headers)
        self.assertEqual(r.status_code, 404)

    def test_todo_delete(self):
        User.create_user(username='username', password='password')
        todo = Todo.create(name='Test Todo', completed=False)
        r = self.app.delete(
            f'/api/v1/todos/{todo.id}',
            headers=BASIC_AUTH_HEADERS)
        self.assertEqual(r.status_code, 204)

    def test_todo_delete_reject(self):
        todo = Todo.create(name='Test Todo', completed=False)
        r = self.app.delete(
            f'/api/v1/todos/{todo.id}',
            headers=BASIC_AUTH_HEADERS)
        self.assertEqual(r.status_code, 401)

    def test_todo_delete_token(self):
        user = User.create_user(username='username', password='password')
        todo = Todo.create(name='Test Todo', completed=False)
        token = user.generate_auth_token().decode('ascii')
        headers = {'Authorization': f'Token {token}'}
        r = self.app.delete(
            f'/api/v1/todos/{todo.id}',
            headers=headers)
        self.assertEqual(r.status_code, 204)

    def test_user_post(self):
        User.create_user(username='username', password='password')
        data = {'username': 'test',
                'password': 'password',
                'verify_password': 'password'}
        r = self.app.post(
            '/api/v1/users',
            data=data,
            headers=BASIC_AUTH_HEADERS)
        self.assertEqual(r.status_code, 201)

    def test_user_post_reject(self):
        User.create_user(username='username', password='password')
        data = {'username': 'test',
                'password': 'password',
                'verify_password': 'drowssap'}
        r = self.app.post(
            '/api/v1/users',
            data=data,
            headers=BASIC_AUTH_HEADERS)
        self.assertEqual(r.status_code, 400)

    def test_get_token(self):
        User.create_user(username='username', password='password')
        r = self.app.get('/api/v1/users/token', headers=BASIC_AUTH_HEADERS)
        self.assertIn('token', r.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
