"""Account isolation, session lifecycle, CSRF and Google verification integration."""
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

_auth_temp = tempfile.TemporaryDirectory()
os.environ.setdefault("RB_DATABASE", str(Path(_auth_temp.name)/"auth-test.sqlite3"))
from fastapi.testclient import TestClient
from app import app, auth, connection
from auth import COOKIE, NONCE_COOKIE, token_hash


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.context = TestClient(app)
        self.client = self.context.__enter__()
        self.headers = {"X-RB-Client":"web"}
        self.registration = {"email":f"qa-{uuid4()}@example.test", "password":"a-good-test-password-123",
                             "name":"تست حساب", "age":28, "city":"تهران"}
        with connection() as db:
            db.execute("DELETE FROM auth_attempts")
            db.commit()

    def tearDown(self):
        self.context.__exit__(None,None,None)

    def post(self, path, body=None):
        return self.client.post('/api/v1/auth'+path,json=body or {},headers=self.headers)

    def test_register_logout_login_and_persistent_private_state(self):
        result = self.post('/register',self.registration)
        self.assertEqual(result.status_code,200,result.text)
        cookie = result.headers['set-cookie']
        self.assertIn('HttpOnly',cookie)
        self.assertIn('SameSite=lax',cookie)
        user = result.json()['user']
        state = self.client.get('/api/v1/state').json()
        self.assertEqual(state['connections'],[])
        self.assertEqual(state['messages'],{})
        self.assertEqual(state['me']['name'],self.registration['name'])
        self.assertEqual(self.client.post('/api/v1/actions',json={'profile_id':'leila','kind':'like'},headers=self.headers).status_code,200)
        token = self.client.cookies.get(COOKIE)
        with connection() as db:
            encoded = db.execute('SELECT password_hash FROM accounts WHERE id=?',(user['id'],)).fetchone()[0]
            self.assertNotIn(self.registration['password'],encoded)
            self.assertNotEqual(db.execute('SELECT token_hash FROM account_sessions WHERE account_id=?',(user['id'],)).fetchone()[0],token)
        self.assertEqual(self.post('/logout').status_code,200)
        credentials = {key:self.registration[key] for key in ('email','password')}
        self.assertEqual(self.post('/login',credentials).status_code,200)
        self.assertNotEqual(self.client.cookies.get(COOKIE),token)
        self.assertIn('leila',self.client.get('/api/v1/state').json()['likes'])

    def test_other_accounts_and_demo_headers_cannot_access_private_state(self):
        first = self.post('/register',self.registration).json()['user']
        self.client.post('/api/v1/actions',json={'profile_id':'demo-001','kind':'like'},headers=self.headers)
        self.post('/logout')
        self.registration['email']=f"other-{uuid4()}@example.test"
        self.post('/register',self.registration)
        own = self.client.get('/api/v1/state',headers={'X-Demo-Session':first['id']}).json()
        self.assertEqual(own['likes'],[])
        self.post('/logout')
        self.assertEqual(self.client.get('/api/v1/state',headers={'X-Demo-Session':'account:'+first['id']}).status_code,400)

    def test_validation_csrf_and_generic_login_errors(self):
        self.assertEqual(self.client.post('/api/v1/auth/register',json=self.registration).status_code,403)
        self.assertEqual(self.client.post('/api/v1/auth/register',json=self.registration,headers={**self.headers,'Origin':'https://evil.invalid'}).status_code,403)
        self.assertEqual(self.post('/register',{**self.registration,'age':17}).status_code,422)
        self.assertEqual(self.post('/register',{**self.registration,'password':'short'}).status_code,422)
        self.assertEqual(self.post('/register',self.registration).status_code,200)
        self.assertEqual(self.client.post('/api/v1/actions',json={'profile_id':'leila','kind':'like'}).status_code,403)
        self.assertEqual(self.post('/register',{**self.registration,'email':self.registration['email'].upper()}).status_code,409)
        self.post('/logout')
        wrong = self.post('/login',{'email':self.registration['email'],'password':'wrong-password-12345'})
        absent = self.post('/login',{'email':'missing@example.test','password':'wrong-password-12345'})
        self.assertEqual(wrong.status_code,401)
        self.assertEqual(wrong.json(),absent.json())

    def test_expired_session_is_rejected_and_status_clears_it(self):
        self.post('/register',self.registration)
        with connection() as db:
            db.execute('UPDATE account_sessions SET expires_at=0 WHERE token_hash=?',(token_hash(self.client.cookies.get(COOKIE)),))
            db.commit()
        self.assertEqual(self.client.get('/api/v1/state',headers={'X-Demo-Session':str(uuid4())}).status_code,401)
        self.assertIsNone(self.client.get('/api/v1/auth/status').json()['user'])
        self.assertIsNone(self.client.cookies.get(COOKIE))

    def test_rate_limit_is_enforced(self):
        for _ in range(20):
            self.assertEqual(self.post('/login',{'email':'absent@example.test','password':'long-invalid-password'}).status_code,401)
        self.assertEqual(self.post('/login',{'email':'absent@example.test','password':'long-invalid-password'}).status_code,429)

    def test_google_is_disabled_without_configuration(self):
        with patch.dict(os.environ,{'RB_GOOGLE_CLIENT_ID':''}):
            self.assertEqual(self.post('/google/challenge').status_code,503)
            self.assertEqual(self.post('/google',{'credential':'invalid','age':28,'city':'تهران'}).status_code,503)

    def test_google_verification_nonce_replay_and_returning_account(self):
        with patch.dict(os.environ,{'RB_GOOGLE_CLIENT_ID':'unit-test.apps.googleusercontent.com'}):
            nonce = self.post('/google/challenge').json()['nonce']
            claims = {'sub':str(uuid4()),'email':f'google-{uuid4()}@example.test','name':'Google Test',
                      'email_verified':True,'nonce':nonce,'aud':os.environ['RB_GOOGLE_CLIENT_ID'],
                      'iss':'https://accounts.google.com','exp':int(time.time())+600}
            body = {'credential':'signed-token-is-mocked-at-verifier','age':29,'city':'تهران'}
            with patch.object(auth,'verify_google',return_value={**claims,'nonce':'bad'}):
                self.assertEqual(self.post('/google',body).status_code,401)
            with patch.object(auth,'verify_google',return_value=claims) as verifier:
                first = self.post('/google',body)
                self.assertEqual(first.status_code,200,first.text)
                verifier.assert_called_with(body['credential'],os.environ['RB_GOOGLE_CLIENT_ID'])
                first_id = first.json()['user']['id']
                self.client.cookies.set(NONCE_COOKIE,nonce,path='/api/v1/auth')
                self.assertEqual(self.post('/google',body).status_code,401)
                self.client.cookies.delete(NONCE_COOKIE)
            self.post('/logout')
            claims['nonce']=self.post('/google/challenge').json()['nonce']
            with patch.object(auth,'verify_google',return_value=claims):
                again = self.post('/google',body)
                self.assertEqual(again.status_code,200,again.text)
                self.assertEqual(again.json()['user']['id'],first_id)

    def test_google_does_not_silently_link_existing_email_account(self):
        self.post('/register',self.registration)
        self.post('/logout')
        with patch.dict(os.environ,{'RB_GOOGLE_CLIENT_ID':'unit-test.apps.googleusercontent.com'}):
            nonce = self.post('/google/challenge').json()['nonce']
            claims = {'sub':str(uuid4()),'email':self.registration['email'],'name':'Test','email_verified':True,
                      'nonce':nonce,'aud':os.environ['RB_GOOGLE_CLIENT_ID'],'iss':'https://accounts.google.com'}
            with patch.object(auth,'verify_google',return_value=claims):
                self.assertEqual(self.post('/google',{'credential':'token','age':28,'city':'تهران'}).status_code,409)


if __name__=='__main__':
    unittest.main()
