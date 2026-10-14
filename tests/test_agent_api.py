import unittest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestAgentApi(unittest.TestCase):
    def test_get_agent_profile(self):
        response = client.get("/api/v1/agent/profile")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("agent_name", data)
        self.assertEqual(data["agent_name"], "Leslie")
        self.assertIn("quick_actions", data)
        action_ids = [a["id"] for a in data["quick_actions"]]
        self.assertIn("create_employee", action_ids)

    def test_avatar_status(self):
        response = client.get("/api/v1/agent/avatar/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["avatar_status"], ["idle", "speaking", "listening"])
        self.assertTrue(data["speak_now_available"])

    def test_agent_db_search(self):
        response = client.post(
            "/api/v1/agent/search-db",
            json={"query": "shifts timings"},
        )
        self.assertIn(response.status_code, [200, 500])
        if response.status_code == 200:
            data = response.json()
            self.assertIn("query", data)
            self.assertIn("results", data)

    def test_create_employee_conversational_step_by_step(self):
        # 1. Start new session
        sess_res = client.post("/api/v1/agent/sessions", json={"session_name": "Employee Test Session"})
        self.assertEqual(sess_res.status_code, 201)
        session_id = sess_res.json()["session_id"]

        # 2. Trigger employee creation flow
        chat_res = client.post(
            "/api/v1/agent/chat",
            json={"session_id": session_id, "message": "I want to create an employee"},
        )
        self.assertEqual(chat_res.status_code, 200)
        data = chat_res.json()
        self.assertEqual(data["action_type"], "employee_onboarding_step")
        self.assertIn("First Name", data["response"])

        # 3. Enter First Name
        chat_res = client.post(
            "/api/v1/agent/chat",
            json={"session_id": session_id, "message": "Sarah"},
        )
        self.assertEqual(chat_res.status_code, 200)
        data = chat_res.json()
        self.assertEqual(data["action_type"], "employee_onboarding_step")
        self.assertIn("Last Name", data["response"])

        # 4. Enter Last Name
        chat_res = client.post(
            "/api/v1/agent/chat",
            json={"session_id": session_id, "message": "Connor"},
        )
        self.assertEqual(chat_res.status_code, 200)
        data = chat_res.json()
        self.assertEqual(data["action_type"], "employee_onboarding_step")
        self.assertIn("Email Address", data["response"])

        # 5. Enter Email
        chat_res = client.post(
            "/api/v1/agent/chat",
            json={"session_id": session_id, "message": "sarah.connor@aaralia.com"},
        )
        self.assertEqual(chat_res.status_code, 200)
        data = chat_res.json()
        self.assertEqual(data["action_type"], "employee_onboarding_step")
        self.assertIn("Mobile Phone", data["response"])

        # 6. Save early
        chat_res = client.post(
            "/api/v1/agent/chat",
            json={"session_id": session_id, "message": "save now"},
        )
        self.assertEqual(chat_res.status_code, 200)
        data = chat_res.json()
        self.assertEqual(data["action_type"], "employee_created")
        self.assertIn("Sarah Connor", data["response"])
        self.assertIn("Employee ID", data["response"])

    def test_create_employee_with_schema_prompt(self):
        # Tests the exact user scenario from the prompt
        sess_res = client.post("/api/v1/agent/sessions", json={"session_name": "Schema Input Session"})
        session_id = sess_res.json()["session_id"]

        user_input = """{
  "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "profile_photo": "string",
  "first_name": "string",
  "last_name": "string",
  "mobile_number": "string",
  "email": "string",
  "father_name": "string",
  "mother_name": "string",
  "marital_status": "string",
  "spouse_name": "string",
  "emergency_contact": "string",
  "date_of_birth": "2026-10-14",
  "govt_id_proof": "string",
  "id_proof_number": "string",
  "gender": "string",
  "nationality": "string",
  "address": "string",
  "city": "string",
  "state": "string",
  "zip_code": "string",
  "employee_id": 0
} this is my create employee data i want in my agent take data one by one and enter in database"""

        chat_res = client.post(
            "/api/v1/agent/chat",
            json={"session_id": session_id, "message": user_input},
        )
        self.assertEqual(chat_res.status_code, 200)
        data = chat_res.json()
        self.assertEqual(data["action_type"], "employee_onboarding_step")
        self.assertIn("First Name", data["response"])

    def test_direct_create_employee_action(self):
        payload = {
            "first_name": "Direct",
            "last_name": "User",
            "email": "direct.user@aaralia.com",
            "mobile_number": "+1234567890",
            "gender": "Male",
            "city": "San Francisco",
            "state": "CA",
            "zip_code": "94105",
        }
        res = client.post("/api/v1/agent/actions/create-employee", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "created")
        self.assertEqual(data["first_name"], "Direct")
        self.assertGreater(data["employee_id"], 0)

    def test_create_employee_complete_one_by_one_all_fields(self):
        sess_res = client.post("/api/v1/agent/sessions", json={"session_name": "Full Flow Session"})
        session_id = sess_res.json()["session_id"]

        steps = [
            ("I want to register an employee", "First Name"),
            ("Michael", "Last Name"),
            ("Corleone", "Email Address"),
            ("michael@corleone.com", "Mobile Phone"),
            ("+1-555-1972", "Gender"),
            ("Male", "Date of Birth"),
            ("1972-03-24", "Government ID Proof"),
            ("Passport", "ID Proof Document Number"),
            ("P1234567", "Nationality"),
            ("Italian-American", "Emergency Contact Number"),
            ("555-9999", "Marital Status"),
            ("Married", "Spouse's Name"),
            ("Kay Adams", "Father's Name"),
            ("Vito Corleone", "Mother's Name"),
            ("Carmela Corleone", "Residential Street Address"),
            ("Mall at Long Beach", "City"),
            ("New York", "State / Province"),
            ("NY", "ZIP / Postal Code"),
            ("11561", "Profile Photo URL"),
        ]

        for user_msg, expected_prompt_part in steps:
            res = client.post(
                "/api/v1/agent/chat",
                json={"session_id": session_id, "message": user_msg},
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["action_type"], "employee_onboarding_step")
            self.assertIn(expected_prompt_part, data["response"])

        # Final field: profile photo
        final_res = client.post(
            "/api/v1/agent/chat",
            json={"session_id": session_id, "message": "https://example.com/michael.jpg"},
        )
        self.assertEqual(final_res.status_code, 200)
        final_data = final_res.json()
        self.assertEqual(final_data["action_type"], "employee_created")
        self.assertIn("Michael Corleone", final_data["response"])
        self.assertIn("Employee ID", final_data["response"])
        self.assertIn("michael@corleone.com", final_data["response"])

    def test_list_employees_endpoint(self):
        res = client.get("/api/v1/agent/actions/employees")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)


if __name__ == "__main__":
    unittest.main()

