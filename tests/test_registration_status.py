import unittest
from unittest.mock import patch

import app as api


EVENT_ID = "123e4567-e89b-12d3-a456-426614174000"
USER_ID = "123e4567-e89b-12d3-a456-426614174001"


class FakeQuery:
    def __init__(self, table, status, inserted):
        self.table_name = table
        self.status = status
        self.inserted = inserted
        self.insert_payload = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def insert(self, payload):
        self.insert_payload = payload
        return self

    def execute(self):
        if self.table_name == "events":
            return type("Result", (), {"data": [{
                "id": EVENT_ID,
                "capacity": None,
                "status": self.status,
            }]})()
        if self.insert_payload:
            self.inserted.append(self.insert_payload)
            return type("Result", (), {"data": [self.insert_payload]})()
        return type("Result", (), {"data": []})()


class FakeSupabase:
    def __init__(self, status):
        self.status = status
        self.inserted = []

    def table(self, table_name):
        return FakeQuery(table_name, self.status, self.inserted)


class RegistrationStatusTests(unittest.TestCase):
    def register(self, status):
        fake_supabase = FakeSupabase(status)
        with patch.object(api, "supabase", fake_supabase):
            response = api.app.test_client().post(
                "/api/registrations",
                json={"user_id": USER_ID, "event_id": EVENT_ID},
            )
        return response, fake_supabase

    def test_upcoming_event_can_be_registered(self):
        response, fake_supabase = self.register("upcoming")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(fake_supabase.inserted), 1)

    def test_closed_event_stays_unavailable(self):
        response, fake_supabase = self.register("closed")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(fake_supabase.inserted, [])


if __name__ == "__main__":
    unittest.main()
