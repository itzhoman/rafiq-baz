"""Behavior checks for state transitions, validation and demo-session isolation."""
import os
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4

_temp = tempfile.TemporaryDirectory()
os.environ["RB_DATABASE"] = str(Path(_temp.name) / "test.sqlite3")
from fastapi.testclient import TestClient
from app import app

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()
        self.headers = {"X-Demo-Session": str(uuid4())}

    def tearDown(self):
        self.client_context.__exit__(None, None, None)

    def post(self, path, body):
        return self.client.post("/api/v1" + path, json=body, headers=self.headers)

    def test_mutual_like_and_session_isolation(self):
        result = self.post("/actions", {"profile_id":"leila","kind":"like"})
        self.assertEqual(result.status_code, 200)
        self.assertIn("leila", result.json()["connections"])
        other = self.client.get("/api/v1/state", headers={"X-Demo-Session":str(uuid4())}).json()
        self.assertNotIn("leila", other["likes"])
        again = self.post("/actions", {"profile_id":"leila","kind":"like"}).json()
        self.assertEqual(again["likes"].count("leila"), 1)

    def test_message_requires_connection_and_preserves_literal_text(self):
        denied = self.post("/messages", {"profile_id":"nika","text":"Hello"})
        self.assertEqual(denied.status_code, 403)
        text = "<script>alert('demo')</script>"
        allowed = self.post("/messages", {"profile_id":"armin","text":text})
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["messages"]["armin"][-1]["text"], text)
        self.assertEqual(self.post("/messages", {"profile_id":"armin","text":"   "}).status_code, 422)

    def test_filters_and_adult_age_validation(self):
        invalid = self.post("/preferences", {"minAge":35,"maxAge":25,"distance":50,"interest":"all","online":False})
        self.assertEqual(invalid.status_code, 422)
        invalid_age = self.post("/me", {"name":"Alex","age":17,"city":"Tehran","bio":"","interests":[]})
        self.assertEqual(invalid_age.status_code, 422)
        valid = self.post("/preferences", {"minAge":25,"maxAge":35,"distance":5,"interest":"coffee","online":True})
        self.assertEqual(valid.json()["preferences"]["distance"], 5)

    def test_save_toggle_pass_undo_and_bad_ids(self):
        body = {"profile_id":"nika","kind":"save"}
        self.assertIn("nika", self.post("/actions", body).json()["saved"])
        self.assertNotIn("nika", self.post("/actions", body).json()["saved"])
        self.post("/actions", {"profile_id":"nika","kind":"pass"})
        state = self.post("/actions", {"profile_id":"nika","kind":"undo"}).json()
        self.assertNotIn("nika", state["passed"])
        self.assertEqual(self.post("/actions", {"profile_id":"missing","kind":"like"}).status_code, 404)

    def test_invalid_session_and_unknown_api_are_not_frontend(self):
        response = self.client.get("/api/v1/state", headers={"X-Demo-Session":"bad"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/api/missing").status_code, 404)

    def test_avoid_feedback_is_separate_reversible_and_session_scoped(self):
        result = self.post("/actions", {"profile_id":"leila","kind":"avoid"})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["avoided"], ["leila"])
        self.assertNotIn("leila", result.json()["passed"])
        again = self.post("/actions", {"profile_id":"leila","kind":"avoid"})
        self.assertEqual(again.json()["avoided"], ["leila"])
        other = self.client.get("/api/v1/state", headers={"X-Demo-Session":str(uuid4())}).json()
        self.assertEqual(other["avoided"], [])
        undone = self.post("/actions", {"profile_id":"leila","kind":"undo_avoid"})
        self.assertEqual(undone.json()["avoided"], [])

    def test_attributes_persist_and_reject_duplicate_keys_and_blanks(self):
        profile = {"name":"Alex","age":29,"city":"Tehran","bio":"Dating intentionally",
                   "interests":["coffee"],"relationshipGoal":"long_term",
                   "attributes":[{"key":"سبک زندگی","value":"آرام"}]}
        saved = self.post("/me", profile)
        self.assertEqual(saved.status_code, 200)
        persisted = self.client.get("/api/v1/state", headers=self.headers).json()
        self.assertEqual(persisted["me"]["attributes"], profile["attributes"])
        self.assertEqual(persisted["me"]["relationshipGoal"], "long_term")
        old_payload = {k:v for k,v in profile.items() if k not in ("attributes","relationshipGoal")}
        self.assertEqual(self.post("/me", old_payload).json()["me"]["attributes"], profile["attributes"])
        profile["attributes"].append({"key":"سبك زندگي","value":"فعال"})
        self.assertEqual(self.post("/me", profile).status_code, 422)
        profile["attributes"] = [{"key":"   ","value":"آرام"}]
        self.assertEqual(self.post("/me", profile).status_code, 422)
        profile["attributes"] = [{"key":"x","value":"y"} for _ in range(13)]
        self.assertEqual(self.post("/me", profile).status_code, 422)

    def test_old_sessions_gain_fields_without_losing_custom_bio(self):
        import json
        from app import connection, DATA
        legacy = json.loads(json.dumps(DATA["state"]))
        legacy.pop("avoided")
        legacy["me"].pop("attributes")
        legacy["me"].pop("relationshipGoal")
        legacy["me"]["bio"] = "Keep my own text"
        with connection() as db:
            db.execute("INSERT INTO sessions(id,state,updated_at) VALUES(?,?,?)",
                       (self.headers["X-Demo-Session"],json.dumps(legacy),"test"))
            db.commit()
        updated = self.client.get("/api/v1/state", headers=self.headers).json()
        self.assertEqual(updated["avoided"], [])
        self.assertEqual(updated["me"]["bio"], "Keep my own text")
        self.assertIsInstance(updated["me"]["attributes"], list)

if __name__ == "__main__":
    unittest.main()
