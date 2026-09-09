import unittest
import uuid
from datetime import date
from fastapi import FastAPI
from fastapi.testclient import TestClient
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.employee_service.models.employee import EmployeeDb
from app.employee_service.models.employee_personal_information import (
    EmployeePersonalInformationDb,
)
from app.employee_service.db.base_class import Base
from app.employee_service.api.deps import get_db
from app.employee_service.api.api_v1.endpoints.employee_personal_information import (
    employee_personal_information_router,
)
from app.user_service.models.user import UsersDb


class TestEmployeePersonalInformationEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine
        )

        for table in Base.metadata.tables.values():
            table.schema = None
        Base.metadata.create_all(bind=cls.engine)

        UsersDb.__table__.schema = None
        UsersDb.metadata.create_all(bind=cls.engine)

        cls.app = FastAPI(title="Employee Personal Info Test App")
        cls.app.include_router(
            employee_personal_information_router,
            prefix="/api/v1",
            tags=["Employee Personal Information"],
        )

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        cls.app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(cls.app)

        # Seed test employees
        db = cls.TestingSessionLocal()
        try:
            for emp_id in [101, 102, 103, 104, 105]:
                emp = EmployeeDb(id=emp_id, employee_code=f"EMP-{emp_id}")
                db.add(emp)
            db.commit()
        finally:
            db.close()

    def setUp(self):
        # Clean personal info table and users table before each test
        db = self.TestingSessionLocal()
        try:
            db.query(EmployeePersonalInformationDb).delete()
            db.query(UsersDb).delete()
            db.commit()
        finally:
            db.close()

    def test_create_personal_info_success(self):
        payload = {
            "employee_id": 101,
            "profile_photo": "https://example.com/photo.jpg",
            "first_name": "Alice",
            "last_name": "Smith",
            "mobile_number": "+1234567890",
            "email": "alice.smith@example.com",
            "father_name": "Bob Smith",
            "mother_name": "Carol Smith",
            "marital_status": "Married",
            "spouse_name": "David Smith",
            "emergency_contact": "+1987654321",
            "date_of_birth": "1990-05-15",
            "govt_id_proof": "Passport",
            "id_proof_number": "A12345678",
            "gender": "Female",
            "nationality": "American",
            "address": "123 Main Street, Apt 4B",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
        }
        response = self.client.post("/api/v1/employee-personal-information", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["employee_id"], 101)
        self.assertEqual(data["first_name"], "Alice")
        self.assertEqual(data["last_name"], "Smith")
        self.assertEqual(data["email"], "alice.smith@example.com")
        self.assertEqual(data["marital_status"], "Married")
        self.assertEqual(data["date_of_birth"], "1990-05-15")
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_create_personal_info_duplicate_409(self):
        payload = {
            "employee_id": 101,
            "first_name": "Alice",
            "email": "alice@example.com",
        }
        res1 = self.client.post("/api/v1/employee-personal-information", json=payload)
        self.assertEqual(res1.status_code, 201)

        res2 = self.client.post("/api/v1/employee-personal-information", json=payload)
        self.assertEqual(res2.status_code, 409)
        self.assertIn("already exists", res2.json()["detail"])

    def test_get_personal_info_by_id_success(self):
        payload = {
            "employee_id": 102,
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob.jones@example.com",
            "city": "San Francisco",
        }
        self.client.post("/api/v1/employee-personal-information", json=payload)

        response = self.client.get("/api/v1/employee-personal-information/102")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["employee_id"], 102)
        self.assertEqual(data["first_name"], "Bob")
        self.assertEqual(data["city"], "San Francisco")

    def test_get_personal_info_not_found_404(self):
        response = self.client.get("/api/v1/employee-personal-information/999")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])

    def test_list_personal_info_pagination_and_search(self):
        employees_data = [
            {"employee_id": 101, "first_name": "Alice", "last_name": "Johnson", "email": "alice@example.com", "city": "Chicago"},
            {"employee_id": 102, "first_name": "Bob", "last_name": "Smith", "email": "bob@example.com", "city": "Boston"},
            {"employee_id": 103, "first_name": "Charlie", "last_name": "Brown", "email": "charlie@example.com", "city": "Austin"},
        ]
        for emp in employees_data:
            self.client.post("/api/v1/employee-personal-information", json=emp)

        # Test listing all
        res = self.client.get("/api/v1/employee-personal-information?skip=0&limit=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 3)
        self.assertEqual(len(data["items"]), 3)

        # Test pagination
        res_page = self.client.get("/api/v1/employee-personal-information?skip=0&limit=2")
        self.assertEqual(res_page.status_code, 200)
        page_data = res_page.json()
        self.assertEqual(page_data["total"], 3)
        self.assertEqual(len(page_data["items"]), 2)
        self.assertEqual(page_data["total_pages"], 2)

        # Test search
        res_search = self.client.get("/api/v1/employee-personal-information?search=Boston")
        self.assertEqual(res_search.status_code, 200)
        search_data = res_search.json()
        self.assertEqual(search_data["total"], 1)
        self.assertEqual(search_data["items"][0]["first_name"], "Bob")

    def test_patch_personal_info_partial_update(self):
        payload = {
            "employee_id": 101,
            "first_name": "Alice",
            "marital_status": "Single",
        }
        self.client.post("/api/v1/employee-personal-information", json=payload)

        update_payload = {
            "marital_status": "Married",
            "spouse_name": "John Doe",
        }
        patch_res = self.client.patch("/api/v1/employee-personal-information/101", json=update_payload)
        self.assertEqual(patch_res.status_code, 200)
        updated = patch_res.json()
        self.assertEqual(updated["marital_status"], "Married")
        self.assertEqual(updated["spouse_name"], "John Doe")
        self.assertEqual(updated["first_name"], "Alice")

    def test_put_personal_info_upsert(self):
        # Upsert when record does not exist
        put_payload = {
            "first_name": "David",
            "last_name": "Miller",
            "city": "Seattle",
        }
        put_res = self.client.put("/api/v1/employee-personal-information/104", json=put_payload)
        self.assertEqual(put_res.status_code, 200)
        data = put_res.json()
        self.assertEqual(data["employee_id"], 104)
        self.assertEqual(data["first_name"], "David")
        self.assertEqual(data["city"], "Seattle")

        # Upsert when record already exists
        update_payload = {
            "city": "Portland",
        }
        put_res2 = self.client.put("/api/v1/employee-personal-information/104", json=update_payload)
        self.assertEqual(put_res2.status_code, 200)
        data2 = put_res2.json()
        self.assertEqual(data2["city"], "Portland")
        self.assertEqual(data2["first_name"], "David")

    def test_delete_personal_info_success(self):
        payload = {
            "employee_id": 105,
            "first_name": "Emma",
        }
        self.client.post("/api/v1/employee-personal-information", json=payload)

        del_res = self.client.delete("/api/v1/employee-personal-information/105")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])
        self.assertEqual(del_res.json()["employee_id"], 105)

        get_res = self.client.get("/api/v1/employee-personal-information/105")
        self.assertEqual(get_res.status_code, 404)

    def test_delete_personal_info_not_found_404(self):
        del_res = self.client.delete("/api/v1/employee-personal-information/999")
        self.assertEqual(del_res.status_code, 404)

    def test_nested_routes(self):
        # Create via nested route
        post_res = self.client.post(
            "/api/v1/employees/101/personal-information",
            json={"first_name": "Fiona", "email": "fiona@example.com"},
        )
        self.assertEqual(post_res.status_code, 201)
        self.assertEqual(post_res.json()["employee_id"], 101)
        self.assertEqual(post_res.json()["first_name"], "Fiona")

        # Get via nested route
        get_res = self.client.get("/api/v1/employees/101/personal-information")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["first_name"], "Fiona")

        # Patch via nested route
        patch_res = self.client.patch(
            "/api/v1/employees/101/personal-information",
            json={"city": "Denver"},
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["city"], "Denver")

        # Delete via nested route
        del_res = self.client.delete("/api/v1/employees/101/personal-information")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

    def test_create_personal_info_with_organization_id_and_auto_user_creation(self):
        org_id = str(uuid.uuid4())
        payload = {
            "employee_id": 101,
            "organization_id": org_id,
            "first_name": "Sarah",
            "last_name": "Connor",
            "email": "sarah.connor@example.com",
            "city": "Los Angeles",
        }
        res = self.client.post("/api/v1/employee-personal-information", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["employee_id"], 101)
        self.assertEqual(data["organization_id"], org_id)
        self.assertEqual(data["first_name"], "Sarah")

        # Verify automatic creation in users table
        db = self.TestingSessionLocal()
        try:
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = db.query(UsersDb).filter(UsersDb.email == "sarah.connor@example.com").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.first_name, "Sarah")
            self.assertEqual(user.last_name, "Connor")
            self.assertEqual(str(user.organization_id), org_id)
            self.assertEqual(user.status, "inactive")
            self.assertFalse(user.is_active)
            # Verify password is "admin"
            self.assertTrue(pwd_context.verify("admin", user.password_salt))
            self.assertTrue(pwd_context.verify("admin", user.password_hash))
        finally:
            db.close()

    def test_filter_by_organization_id(self):
        org_a = str(uuid.uuid4())
        org_b = str(uuid.uuid4())

        # Org A employees
        self.client.post(
            "/api/v1/employee-personal-information",
            json={"employee_id": 101, "first_name": "Alice", "organization_id": org_a},
        )
        self.client.post(
            "/api/v1/employee-personal-information",
            json={"employee_id": 102, "first_name": "Bob", "organization_id": org_a},
        )
        # Org B employee
        self.client.post(
            "/api/v1/employee-personal-information",
            json={"employee_id": 103, "first_name": "Charlie", "organization_id": org_b},
        )

        # 1. Filter via query parameter on /employee-personal-information
        res_a = self.client.get(f"/api/v1/employee-personal-information?organization_id={org_a}")
        self.assertEqual(res_a.status_code, 200)
        data_a = res_a.json()
        self.assertEqual(data_a["total"], 2)
        names_a = [item["first_name"] for item in data_a["items"]]
        self.assertIn("Alice", names_a)
        self.assertIn("Bob", names_a)

        # 2. Filter via /organizations/{organization_id}/employee-personal-information
        res_a_endpoint = self.client.get(f"/api/v1/organizations/{org_a}/employee-personal-information")
        self.assertEqual(res_a_endpoint.status_code, 200)
        self.assertEqual(res_a_endpoint.json()["total"], 2)

        # 3. Filter Org B via /employee-personal-information/organization/{organization_id}
        res_b = self.client.get(f"/api/v1/employee-personal-information/organization/{org_b}")
        self.assertEqual(res_b.status_code, 200)
        data_b = res_b.json()
        self.assertEqual(data_b["total"], 1)
        self.assertEqual(data_b["items"][0]["first_name"], "Charlie")

    def test_update_personal_info_organization_id(self):
        org_1 = str(uuid.uuid4())
        org_2 = str(uuid.uuid4())

        post_res = self.client.post(
            "/api/v1/employee-personal-information",
            json={
                "employee_id": 104,
                "first_name": "David",
                "email": "david@example.com",
                "organization_id": org_1,
            },
        )
        self.assertEqual(post_res.status_code, 201)

        # Patch organization_id to org_2
        patch_res = self.client.patch(
            "/api/v1/employee-personal-information/104",
            json={"organization_id": org_2},
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["organization_id"], org_2)

        # Verify user record is also synced with new organization_id
        db = self.TestingSessionLocal()
        try:
            user = db.query(UsersDb).filter(UsersDb.email == "david@example.com").first()
            self.assertIsNotNone(user)
            self.assertEqual(str(user.organization_id), org_2)
            self.assertEqual(user.status, "inactive")
            self.assertFalse(user.is_active)
        finally:
            db.close()

    def test_put_upsert_creates_user_with_admin_password_and_inactive_status(self):
        org_id = str(uuid.uuid4())
        res = self.client.put(
            "/api/v1/employee-personal-information/105",
            json={
                "first_name": "Eve",
                "last_name": "Adams",
                "email": "eve.adams@example.com",
                "organization_id": org_id,
            },
        )
        self.assertEqual(res.status_code, 200)

        db = self.TestingSessionLocal()
        try:
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = db.query(UsersDb).filter(UsersDb.email == "eve.adams@example.com").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.first_name, "Eve")
            self.assertEqual(user.last_name, "Adams")
            self.assertEqual(str(user.organization_id), org_id)
            self.assertEqual(user.status, "inactive")
            self.assertFalse(user.is_active)
            self.assertTrue(pwd_context.verify("admin", user.password_salt))
            self.assertTrue(pwd_context.verify("admin", user.password_hash))
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()

