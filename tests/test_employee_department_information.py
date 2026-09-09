import unittest
from decimal import Decimal
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.employee_service.models.employee import EmployeeDb
from app.employee_service.models.employee_department_information import (
    EmployeeDepartmentInformationDb,
)
from app.employee_service.db.base_class import Base
from app.employee_service.api.deps import get_db
from app.employee_service.api.api_v1.endpoints.employee_department_information import (
    employee_department_information_router,
)


class TestEmployeeDepartmentInformationEndpoints(unittest.TestCase):
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
        EmployeeDepartmentInformationDb.__table__.schema = None
        Base.metadata.create_all(bind=cls.engine)

        cls.app = FastAPI(title="Employee Department Info Test App")
        cls.app.include_router(
            employee_department_information_router,
            prefix="/api/v1",
            tags=["Employee Department Information"],
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
            for emp_id in [301, 302, 303, 304, 305, 999]:
                emp = EmployeeDb(id=emp_id, employee_code=f"EMP-{emp_id}")
                db.add(emp)
            db.commit()
        finally:
            db.close()

    def setUp(self):
        db = self.TestingSessionLocal()
        try:
            db.query(EmployeeDepartmentInformationDb).delete()
            db.commit()
        finally:
            db.close()

    def test_create_department_info_success(self):
        payload = {
            "employee_id": 301,
            "department": "Engineering",
            "designation": "Senior Software Engineer",
            "reporting_manager_id": 999,
            "work_location": "San Francisco",
            "work_mode": "Hybrid",
            "employment_type": "Full Time",
            "ctc_offered": 150000.00,
        }
        response = self.client.post("/api/v1/employee-department-information", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["employee_id"], 301)
        self.assertEqual(data["department"], "Engineering")
        self.assertEqual(data["designation"], "Senior Software Engineer")
        self.assertEqual(data["reporting_manager_id"], 999)
        self.assertEqual(data["work_mode"], "Hybrid")
        self.assertEqual(data["employment_type"], "Full Time")
        self.assertEqual(float(data["ctc_offered"]), 150000.0)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_create_department_info_duplicate_409(self):
        payload = {
            "employee_id": 301,
            "department": "Engineering",
        }
        res1 = self.client.post("/api/v1/employee-department-information", json=payload)
        self.assertEqual(res1.status_code, 201)

        res2 = self.client.post("/api/v1/employee-department-information", json=payload)
        self.assertEqual(res2.status_code, 409)
        self.assertIn("already exists", res2.json()["detail"])

    def test_get_department_info_by_id_success(self):
        payload = {
            "employee_id": 302,
            "department": "Product",
            "designation": "Product Manager",
        }
        self.client.post("/api/v1/employee-department-information", json=payload)

        response = self.client.get("/api/v1/employee-department-information/302")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["employee_id"], 302)
        self.assertEqual(data["department"], "Product")

    def test_get_department_info_not_found_404(self):
        response = self.client.get("/api/v1/employee-department-information/888")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])

    def test_list_department_info_pagination_and_search(self):
        records = [
            {"employee_id": 301, "department": "Marketing", "designation": "Specialist", "work_location": "Chicago"},
            {"employee_id": 302, "department": "Finance", "designation": "Analyst", "work_location": "New York"},
            {"employee_id": 303, "department": "Marketing", "designation": "Lead", "work_location": "Austin"},
        ]
        for r in records:
            self.client.post("/api/v1/employee-department-information", json=r)

        # List all
        res = self.client.get("/api/v1/employee-department-information?skip=0&limit=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 3)
        self.assertEqual(len(data["items"]), 3)

        # Search filter
        res_search = self.client.get("/api/v1/employee-department-information?search=Finance")
        self.assertEqual(res_search.status_code, 200)
        search_data = res_search.json()
        self.assertEqual(search_data["total"], 1)
        self.assertEqual(search_data["items"][0]["department"], "Finance")

    def test_patch_department_info_partial_update(self):
        payload = {
            "employee_id": 301,
            "department": "Design",
            "designation": "Junior Designer",
        }
        self.client.post("/api/v1/employee-department-information", json=payload)

        patch_res = self.client.patch(
            "/api/v1/employee-department-information/301",
            json={"designation": "Lead Designer", "work_mode": "Remote"},
        )
        self.assertEqual(patch_res.status_code, 200)
        updated = patch_res.json()
        self.assertEqual(updated["designation"], "Lead Designer")
        self.assertEqual(updated["work_mode"], "Remote")
        self.assertEqual(updated["department"], "Design")

    def test_put_department_info_upsert(self):
        # Insert via PUT
        put_payload = {
            "department": "Human Resources",
            "designation": "HR Manager",
            "work_location": "Seattle",
        }
        put_res = self.client.put("/api/v1/employee-department-information/304", json=put_payload)
        self.assertEqual(put_res.status_code, 200)
        data = put_res.json()
        self.assertEqual(data["employee_id"], 304)
        self.assertEqual(data["department"], "Human Resources")

        # Update via PUT
        put_res2 = self.client.put(
            "/api/v1/employee-department-information/304",
            json={"department": "People & Culture"},
        )
        self.assertEqual(put_res2.status_code, 200)
        self.assertEqual(put_res2.json()["department"], "People & Culture")

    def test_delete_department_info_success(self):
        payload = {
            "employee_id": 305,
            "department": "Legal",
        }
        self.client.post("/api/v1/employee-department-information", json=payload)

        del_res = self.client.delete("/api/v1/employee-department-information/305")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

        get_res = self.client.get("/api/v1/employee-department-information/305")
        self.assertEqual(get_res.status_code, 404)

    def test_delete_department_info_not_found_404(self):
        del_res = self.client.delete("/api/v1/employee-department-information/888")
        self.assertEqual(del_res.status_code, 404)

    def test_nested_routes(self):
        # Create via nested
        post_res = self.client.post(
            "/api/v1/employees/301/department-information",
            json={"department": "Operations", "designation": "Ops Lead"},
        )
        self.assertEqual(post_res.status_code, 201)
        self.assertEqual(post_res.json()["employee_id"], 301)
        self.assertEqual(post_res.json()["department"], "Operations")

        # Get via nested
        get_res = self.client.get("/api/v1/employees/301/department-information")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["department"], "Operations")

        # Patch via nested
        patch_res = self.client.patch(
            "/api/v1/employees/301/department-information",
            json={"work_mode": "Onsite"},
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["work_mode"], "Onsite")

        # Delete via nested
        del_res = self.client.delete("/api/v1/employees/301/department-information")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])


if __name__ == "__main__":
    unittest.main()
