import os
import birds
import unittest
import tempfile
from birds.birds import *


class BirdsTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, birds.app.config['DATABASE'] = tempfile.mkstemp()
        birds.app.config['TESTING'] = True
        self.app = birds.app.test_client()
        with birds.app.app_context():
            birds.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(birds.app.config['DATABASE'])

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)




    def test_empty_db(self):
        rv = self.app.get('/')
        assert b'No entries here so far' in rv.data

    def test_login_logout(self):
        rv = self.login('admin', 'default')
        assert b'You were logged in' in rv.data
        rv = self.logout()
        assert b'You were logged out' in rv.data
        rv = self.login('adminx', 'default')
        assert b'Invalid username' in rv.data
        rv = self.login('admin', 'defaultx')
        assert b'Invalid password' in rv.data


if __name__ == '__main__':
    unittest.main()