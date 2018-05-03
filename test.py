import unittest


import app


class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.app.test_client()

    def test_get_todo_list(self):
        r = self.app.get('/')
        self.assertEqual(r.status_code, 200)

    def test_post_todo(self):
        data = {'name': 'Test Todo'}
        r = self.app.post('/api/v1/todos', data=data, follow_redirects=True)
        self.assertEqual(r.status_code, 201)


if __name__ == '__main__':
    unittest.main()
