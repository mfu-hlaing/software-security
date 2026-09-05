"""Real request flow checks for the deliberately vulnerable NoteVault starter.

Run inside the pinned target image: python -m unittest discover -s tests.
These assertions preserve the assignment's behavior; they do not certify security.
"""
import unittest
import app


class NoteVaultWorkflow(unittest.TestCase):
    def setUp(self):
        app.app.config['TESTING'] = True
        app.seed()
        self.client = app.app.test_client()

    def login(self):
        return self.client.post('/login', data={'username': 'alice', 'password': 'alicepw'})

    def test_signin_and_static_assets(self):
        page = self.client.get('/')
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'Open your notebook.', page.data)
        self.assertEqual(self.client.get('/static/notevault.css').status_code, 200)
        self.assertEqual(self.client.get('/api/notes/1').status_code, 401)

    def test_failed_login_is_a_usable_page(self):
        page = self.client.post('/login', data={'username': 'alice', 'password': 'wrong'})
        self.assertEqual(page.status_code, 401)
        self.assertIn(b'role="alert"', page.data)
        self.assertIn(b'action="/login"', page.data)

    def test_create_search_and_json_roundtrip(self):
        self.assertEqual(self.login().status_code, 302)
        saved = self.client.post('/notes', data={'title': 'Boundary notes', 'body': 'request trace'}, follow_redirects=True)
        self.assertIn(b'Boundary notes', saved.data)
        self.assertIn(b'Your notebook, alice.', saved.data)
        self.assertIn(b'Boundary notes', self.client.get('/search?q=trace').data)
        self.assertNotIn(b'Boundary notes', self.client.get('/search?q=absent').data)
        self.assertEqual(self.client.get('/api/notes/4').json['body'], 'request trace')

    def test_logout_clears_the_app_session(self):
        self.login()
        self.client.get('/logout')
        self.assertEqual(self.client.get('/api/notes/1').status_code, 401)

    def test_registration_then_signin(self):
        self.client.post('/register', data={'username': 'learner', 'password': 'fictional', 'role': 'user'})
        page = self.client.post('/login', data={'username': 'learner', 'password': 'fictional'}, follow_redirects=True)
        self.assertIn(b'A fresh page awaits', page.data)

    def test_raw_note_rendering_remains_an_exercise(self):
        self.login()
        self.client.post('/notes', data={'title': 'Rendering test', 'body': '<em data-probe="demo">marker</em>'})
        self.assertIn(b'<em data-probe="demo">marker</em>', self.client.get('/').data)

    def test_search_template_behavior_remains_an_exercise(self):
        self.login()
        self.client.post('/notes', data={'title': 'Expression', 'body': '{{ 7*7 }}'})
        self.assertIn(b'49</div>', self.client.get('/search?q=7').data)

    def test_object_policy_remains_the_project_assignment(self):
        self.login()
        self.assertEqual(self.client.get('/api/notes/2').json['owner'], 'admin')
        self.assertEqual(self.client.get('/admin').status_code, 403)
        self.assertIn(b'exporting notes as txt', self.client.get('/export?fmt=txt').data)


if __name__ == '__main__':
    unittest.main()
