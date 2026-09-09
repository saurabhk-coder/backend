import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.employee_service.models.employee import EmployeeDb
from app.employee_service.models.employee_account_details import (
    EmployeeAccountDetailsDb,
)
from app.employee_service.db.base_class import Base
from app.employee_service.api.deps import get_db
from app.employee_service.api.api_v1.endpoints.employee_account_details import (
    employee_account_details_router,
)


class TestEmployeeAccountDetailsEndpoints(unittest.TestCase):
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

        EmployeeDb.__table__.schema = None
        EmployeeAccountDetailsDb.__table__.schema = None
        Base.metadata.create_all(bind=cls.engine)

        cls.app = FastAPI(title="Employee Account Details Test App")
        cls.app.include_router(
            employee_account_details_router,
            prefix="/api/v1",
            tags=["Employee Account Details"],
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
            for emp_id in [201, 202, 203, 204, 205]:
                emp = EmployeeDb(id=emp_id, employee_code=f"EMP-{emp_id}")
                db.add(emp)
            db.commit()
        finally:
            db.close()

    def setUp(self):
        db = self.TestingSessionLocal()
        try:
            db.query(EmployeeAccountDetailsDb).delete()
            db.commit()
        finally:
            db.close()

    def test_create_account_details_success(self):
        payload = {
            "employee_id": 201,
            "bank_name": "Chase Bank",
            "ifsc_code": "CHAS0001234",
            "account_number": "123456789012",
        }
        response = self.client.post("/api/v1/employee-account-details", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["employee_id"], 201)
        self.assertEqual(data["bank_name"], "Chase Bank")
        self.assertEqual(data["ifsc_code"], "CHAS0001234")
        self.assertEqual(data["account_number"], "123456789012")
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_create_account_details_duplicate_409(self):
        payload = {
            "employee_id": 201,
            "bank_name": "Chase Bank",
            "account_number": "123456789012",
        }
        res1 = self.client.post("/api/v1/employee-account-details", json=payload)
        self.assertEqual(res1.status_code, 201)

        res2 = self.client.post("/api/v1/employee-account-details", json=payload)
        self.assertEqual(res2.status_code, 409)
        self.assertIn("already exist", res2.json()["detail"])

    def test_get_account_details_by_id_success(self):
        payload = {
            "employee_id": 202,
            "bank_name": "Bank of America",
            "account_number": "987654321098",
        }
        self.client.post("/api/v1/employee-account-details", json=payload)

        response = self.client.get("/api/v1/employee-account-details/202")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["employee_id"], 202)
        self.assertEqual(data["bank_name"], "Bank of America")

    def test_get_account_details_not_found_404(self):
        response = self.client.get("/api/v1/employee-account-details/999")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])

    def test_list_account_details_pagination_and_search(self):
        records = [
            {"employee_id": 201, "bank_name": "Wells Fargo", "ifsc_code": "WF001", "account_number": "1111"},
            {"employee_id": 202, "bank_name": "Citibank", "ifsc_code": "CITI002", "account_number": "2222"},
            {"employee_id": 203, "bank_name": "Wells Fargo", "ifsc_code": "WF003", "account_number": "3333"},
        ]
        for r in records:
            self.client.post("/api/v1/employee-account-details", json=r)

        # List all
        res = self.client.get("/api/v1/employee-account-details?skip=0&limit=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 3)
        self.assertEqual(len(data["items"]), 3)

        # Search filter
        res_search = self.client.get("/api/v1/employee-account-details?search=Citibank")
        self.assertEqual(res_search.status_code, 200)
        search_data = res_search.json()
        self.assertEqual(search_data["total"], 1)
        self.assertEqual(search_data["items"][0]["bank_name"], "Citibank")

    def test_patch_account_details_partial_update(self):
        payload = {
            "employee_id": 201,
            "bank_name": "PNC Bank",
            "account_number": "111122223333",
        }
        self.client.post("/api/v1/employee-account-details", json=payload)

        patch_res = self.client.patch(
            "/api/v1/employee-account-details/201",
            json={"ifsc_code": "PNC0009999"},
        )
        self.assertEqual(patch_res.status_code, 200)
        updated = patch_res.json()
        self.assertEqual(updated["ifsc_code"], "PNC0009999")
        self.assertEqual(updated["bank_name"], "PNC Bank")

    def test_put_account_details_upsert(self):
        # Insert via PUT
        put_payload = {
            "bank_name": "Barclays",
            "account_number": "444455556666",
        }
        put_res = self.client.put("/api/v1/employee-account-details/204", json=put_payload)
        self.assertEqual(put_res.status_code, 200)
        data = put_res.json()
        self.assertEqual(data["employee_id"], 204)
        self.assertEqual(data["bank_name"], "Barclays")

        # Update via PUT
        put_res2 = self.client.put(
            "/api/v1/employee-account-details/204",
            json={"bank_name": "Barclays International"},
        )
        self.assertEqual(put_res2.status_code, 200)
        self.assertEqual(put_res2.json()["bank_name"], "Barclays International")

    def test_delete_account_details_success(self):
        payload = {
            "employee_id": 205,
            "bank_name": "HSBC",
        }
        self.client.post("/api/v1/employee-account-details", json=payload)

        del_res = self.client.delete("/api/v1/employee-account-details/205")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

        get_res = self.client.get("/api/v1/employee-account-details/205")
        self.assertEqual(get_res.status_code, 404)

    def test_delete_account_details_not_found_404(self):
        del_res = self.client.delete("/api/v1/employee-account-details/999")
        self.assertEqual(del_res.status_code, 404)

    def test_nested_routes(self):
        # Create via nested
        post_res = self.client.post(
            "/api/v1/employees/201/account-details",
            json={"bank_name": "Capital One", "account_number": "777788889999"},
        )
        self.assertEqual(post_res.status_code, 201)
        self.assertEqual(post_res.json()["employee_id"], 201)
        self.assertEqual(post_res.json()["bank_name"], "Capital One")

        # Get via nested
        get_res = self.client.get("/api/v1/employees/201/account-details")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["bank_name"], "Capital One")

        # Patch via nested
        patch_res = self.client.patch(
            "/api/v1/employees/201/account-details",
            json={"ifsc_code": "CAP001"},
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["ifsc_code"], "CAP001")

        # Delete via nested
        del_res = self.client.delete("/api/v1/employees/201/account-details")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])


if __name__ == "__main__":
    unittest.main()
