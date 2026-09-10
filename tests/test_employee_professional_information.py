import unittest
from decimal import Decimal
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.employee_service.models.employee import EmployeeDb
from app.employee_service.models.employee_professional_information import (
    EmployeeProfessionalInformationDb,
)
from app.employee_service.db.base_class import Base
from app.employee_service.api.deps import get_db
from app.employee_service.api.api_v1.endpoints.employee_professional_information import (
    employee_professional_information_router,
)


class TestEmployeeProfessionalInformationEndpoints(unittest.TestCase):
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

        cls.app = FastAPI(title="Employee Professional Info Test App")
        cls.app.include_router(
            employee_professional_information_router,
            prefix="/api/v1",
            tags=["Employee Professional Information"],
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
            for emp_id in [401, 402, 403, 404, 405, 999]:
                emp = EmployeeDb(id=emp_id, employee_code=f"EMP-{emp_id}")
                db.add(emp)
            db.commit()
        finally:
            db.close()

    def setUp(self):
        db = self.TestingSessionLocal()
        try:
            db.query(EmployeeProfessionalInformationDb).delete()
            db.commit()
        finally:
            db.close()

    def test_create_professional_info_success(self):
        payload = {
            "employee_id": 401,
            "tenth_roll": "10TH-12345",
            "tenth_percentage_cgpa": "88.5%",
            "twelfth_roll": "12TH-67890",
            "twelfth_percentage_cgpa": "91.2%",
            "graduation_roll": "BTECH-456",
            "graduation_percentage_cgpa": "8.5 CGPA",
            "post_graduation_roll": "MTECH-789",
            "post_graduation_percentage_cgpa": "8.9 CGPA",
            "total_experience_years": "4.5",
            "last_company_details": "Tech Solutions Inc, Senior Developer",
            "last_ctc": 1200000.00,
            "certifications": "AWS Certified Solutions Architect, CKA",
            "skills": "Python, FastAPI, PostgreSQL, Docker, Kubernetes",
        }
        response = self.client.post(
            "/api/v1/employee-professional-information", json=payload
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["employee_id"], 401)
        self.assertEqual(data["tenth_roll"], "10TH-12345")
        self.assertEqual(data["tenth_percentage_cgpa"], "88.5%")
        self.assertEqual(data["twelfth_roll"], "12TH-67890")
        self.assertEqual(data["twelfth_percentage_cgpa"], "91.2%")
        self.assertEqual(data["graduation_roll"], "BTECH-456")
        self.assertEqual(data["graduation_percentage_cgpa"], "8.5 CGPA")
        self.assertEqual(data["post_graduation_roll"], "MTECH-789")
        self.assertEqual(data["post_graduation_percentage_cgpa"], "8.9 CGPA")
        self.assertEqual(float(data["total_experience_years"]), 4.5)
        self.assertEqual(data["last_company_details"], "Tech Solutions Inc, Senior Developer")
        self.assertEqual(float(data["last_ctc"]), 1200000.0)
        self.assertEqual(data["certifications"], "AWS Certified Solutions Architect, CKA")
        self.assertEqual(data["skills"], "Python, FastAPI, PostgreSQL, Docker, Kubernetes")
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_create_professional_info_duplicate_409(self):
        payload = {
            "employee_id": 401,
            "tenth_roll": "10TH-12345",
            "skills": "Python, Go",
        }
        res1 = self.client.post(
            "/api/v1/employee-professional-information", json=payload
        )
        self.assertEqual(res1.status_code, 201)

        res2 = self.client.post(
            "/api/v1/employee-professional-information", json=payload
        )
        self.assertEqual(res2.status_code, 409)
        self.assertIn("already exists", res2.json()["detail"])

    def test_get_professional_info_by_id_success(self):
        payload = {
            "employee_id": 402,
            "graduation_roll": "GRAD-2020",
            "skills": "React, TypeScript",
        }
        self.client.post(
            "/api/v1/employee-professional-information", json=payload
        )

        response = self.client.get(
            "/api/v1/employee-professional-information/402"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["employee_id"], 402)
        self.assertEqual(data["graduation_roll"], "GRAD-2020")
        self.assertEqual(data["skills"], "React, TypeScript")

    def test_get_professional_info_not_found_404(self):
        response = self.client.get(
            "/api/v1/employee-professional-information/888"
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])

    def test_list_professional_info_pagination_and_search(self):
        records = [
            {
                "employee_id": 401,
                "graduation_roll": "CS-001",
                "skills": "Python, Django",
                "last_company_details": "Alpha Corp",
            },
            {
                "employee_id": 402,
                "graduation_roll": "ME-002",
                "skills": "Java, Spring Boot",
                "last_company_details": "Beta Ltd",
            },
            {
                "employee_id": 403,
                "graduation_roll": "CS-003",
                "skills": "Python, Machine Learning",
                "last_company_details": "Gamma AI",
            },
        ]
        for r in records:
            self.client.post(
                "/api/v1/employee-professional-information", json=r
            )

        # List all
        res = self.client.get(
            "/api/v1/employee-professional-information?skip=0&limit=10"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 3)
        self.assertEqual(len(data["items"]), 3)

        # Search filter by skill
        res_search = self.client.get(
            "/api/v1/employee-professional-information?search=Machine Learning"
        )
        self.assertEqual(res_search.status_code, 200)
        search_data = res_search.json()
        self.assertEqual(search_data["total"], 1)
        self.assertEqual(search_data["items"][0]["employee_id"], 403)

        # Search filter by company
        res_search_company = self.client.get(
            "/api/v1/employee-professional-information?search=Beta"
        )
        self.assertEqual(res_search_company.status_code, 200)
        self.assertEqual(res_search_company.json()["total"], 1)
        self.assertEqual(
            res_search_company.json()["items"][0]["employee_id"], 402
        )

    def test_patch_professional_info_partial_update(self):
        payload = {
            "employee_id": 401,
            "tenth_roll": "ROLL-10",
            "skills": "C++",
        }
        self.client.post(
            "/api/v1/employee-professional-information", json=payload
        )

        patch_res = self.client.patch(
            "/api/v1/employee-professional-information/401",
            json={
                "skills": "Rust, Go",
                "total_experience_years": 3.0,
            },
        )
        self.assertEqual(patch_res.status_code, 200)
        updated = patch_res.json()
        self.assertEqual(updated["skills"], "Rust, Go")
        self.assertEqual(float(updated["total_experience_years"]), 3.0)
        self.assertEqual(updated["tenth_roll"], "ROLL-10")

    def test_put_professional_info_upsert(self):
        # Insert via PUT when not exists
        put_payload = {
            "skills": "Kubernetes, Helm, Terraform",
            "last_company_details": "Cloud Native Corp",
            "total_experience_years": 6.0,
        }
        put_res = self.client.put(
            "/api/v1/employee-professional-information/404",
            json=put_payload,
        )
        self.assertEqual(put_res.status_code, 200)
        data = put_res.json()
        self.assertEqual(data["employee_id"], 404)
        self.assertEqual(data["skills"], "Kubernetes, Helm, Terraform")

        # Update via PUT when exists
        put_res2 = self.client.put(
            "/api/v1/employee-professional-information/404",
            json={
                "skills": "DevOps Architect, AWS, GCP",
                "last_company_details": "Cloud Native Corp",
            },
        )
        self.assertEqual(put_res2.status_code, 200)
        self.assertEqual(
            put_res2.json()["skills"], "DevOps Architect, AWS, GCP"
        )

    def test_delete_professional_info_success(self):
        payload = {
            "employee_id": 405,
            "skills": "QA, Selenium, Cypress",
        }
        self.client.post(
            "/api/v1/employee-professional-information", json=payload
        )

        del_res = self.client.delete(
            "/api/v1/employee-professional-information/405"
        )
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

        get_res = self.client.get(
            "/api/v1/employee-professional-information/405"
        )
        self.assertEqual(get_res.status_code, 404)

    def test_delete_professional_info_not_found_404(self):
        del_res = self.client.delete(
            "/api/v1/employee-professional-information/888"
        )
        self.assertEqual(del_res.status_code, 404)

    def test_nested_routes(self):
        # Create via nested POST
        post_res = self.client.post(
            "/api/v1/employees/401/professional-information",
            json={
                "graduation_roll": "BCA-101",
                "skills": "Frontend, Vue.js",
            },
        )
        self.assertEqual(post_res.status_code, 201)
        self.assertEqual(post_res.json()["employee_id"], 401)
        self.assertEqual(post_res.json()["graduation_roll"], "BCA-101")
        self.assertEqual(post_res.json()["skills"], "Frontend, Vue.js")

        # Get via nested GET
        get_res = self.client.get(
            "/api/v1/employees/401/professional-information"
        )
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["graduation_roll"], "BCA-101")

        # Patch via nested PATCH
        patch_res = self.client.patch(
            "/api/v1/employees/401/professional-information",
            json={"skills": "Frontend, Vue.js, Nuxt"},
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(
            patch_res.json()["skills"], "Frontend, Vue.js, Nuxt"
        )

        # Upsert via nested PUT
        put_res = self.client.put(
            "/api/v1/employees/401/professional-information",
            json={
                "graduation_roll": "BCA-101",
                "skills": "Fullstack Engineer",
            },
        )
        self.assertEqual(put_res.status_code, 200)
        self.assertEqual(put_res.json()["skills"], "Fullstack Engineer")

        # Delete via nested DELETE
        del_res = self.client.delete(
            "/api/v1/employees/401/professional-information"
        )
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])


if __name__ == "__main__":
    unittest.main()
