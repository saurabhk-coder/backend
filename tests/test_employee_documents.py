import io
import unittest
import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.employee_service.models.employee import EmployeeDb
from app.employee_service.models.employee_document import EmployeeDocumentDb
from app.employee_service.db.base_class import Base
from app.employee_service.api.deps import get_db
from app.employee_service.api.api_v1.endpoints.employee_documents import (
    employee_documents_router,
)


class TestEmployeeDocumentsEndpoints(unittest.TestCase):
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

        cls.app = FastAPI(title="Employee Documents Test App")
        cls.app.include_router(
            employee_documents_router,
            prefix="/api/v1",
            tags=["Employee Documents"],
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
            for emp_id in [401, 402, 403]:
                emp = EmployeeDb(id=emp_id, employee_code=f"EMP-{emp_id}")
                db.add(emp)
            db.commit()
        finally:
            db.close()

    def setUp(self):
        db = self.TestingSessionLocal()
        try:
            db.query(EmployeeDocumentDb).delete()
            db.commit()
        finally:
            db.close()

    def test_get_categories(self):
        response = self.client.get("/api/v1/employee-documents/categories")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        category_ids = [cat["id"] for cat in data]
        self.assertIn("govt_id_proof", category_ids)
        self.assertIn("profile_photo", category_ids)
        self.assertIn("resume", category_ids)
        self.assertIn("contract", category_ids)

    def test_upload_employee_document(self):
        file_content = b"%PDF-1.4 test employee offer letter content"
        files = {
            "file": ("offer_letter.pdf", io.BytesIO(file_content), "application/pdf")
        }
        data = {
            "file_title": "Offer Letter 2026",
            "file_category": "contract",
            "description": "Signed offer letter",
        }
        response = self.client.post(
            "/api/v1/employees/401/documents/upload",
            files=files,
            data=data,
        )
        self.assertEqual(response.status_code, 201)
        res_json = response.json()
        self.assertEqual(res_json["employee_id"], 401)
        self.assertEqual(res_json["file_name"], "offer_letter.pdf")
        self.assertEqual(res_json["file_title"], "Offer Letter 2026")
        self.assertEqual(res_json["file_category"], "contract")
        self.assertEqual(res_json["gcs_bucket"], "hrms-aaralia")
        self.assertTrue(res_json["gcs_blob_name"].startswith("employees/401/contract/"))
        self.assertIsNotNone(res_json["download_url"])

    def test_employee_can_view_uploaded_files(self):
        # 1. Upload first document
        file_1 = b"Identity Proof Aadhaar card content"
        self.client.post(
            "/api/v1/employees/401/documents/upload",
            files={"file": ("aadhaar.pdf", io.BytesIO(file_1), "application/pdf")},
            data={"file_title": "Aadhaar Card", "file_category": "govt_id_proof"},
        )

        # 2. Upload second document
        file_2 = b"Resume content here"
        self.client.post(
            "/api/v1/employees/401/documents/upload",
            files={"file": ("resume.pdf", io.BytesIO(file_2), "application/pdf")},
            data={"file_title": "Resume 2026", "file_category": "resume"},
        )

        # 3. Employee 401 views their uploaded files
        response = self.client.get("/api/v1/employees/401/documents")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["employee_id"], 401)
        self.assertEqual(len(data["items"]), 2)
        # Check signed/direct download URLs are included
        for item in data["items"]:
            self.assertIsNotNone(item["download_url"])

        # 4. Filter by category
        res_cat = self.client.get("/api/v1/employees/401/documents?category=govt_id_proof")
        self.assertEqual(res_cat.status_code, 200)
        data_cat = res_cat.json()
        self.assertEqual(data_cat["total"], 1)
        self.assertEqual(data_cat["items"][0]["file_category"], "govt_id_proof")

        # 5. Other employee has 0 documents
        res_other = self.client.get("/api/v1/employees/402/documents")
        self.assertEqual(res_other.status_code, 200)
        self.assertEqual(res_other.json()["total"], 0)

    def test_get_document_by_id_and_download(self):
        file_content = b"Binary certificate content for employee"
        upload_res = self.client.post(
            "/api/v1/employees/401/documents/upload",
            files={"file": ("cert.pdf", io.BytesIO(file_content), "application/pdf")},
            data={"file_title": "Degree Certificate", "file_category": "certificate"},
        )
        self.assertEqual(upload_res.status_code, 201)
        doc_id = upload_res.json()["id"]

        # Get document by ID
        get_res = self.client.get(f"/api/v1/employee-documents/{doc_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["file_title"], "Degree Certificate")

        # Download file content
        dl_res = self.client.get(f"/api/v1/employee-documents/{doc_id}/download")
        self.assertEqual(dl_res.status_code, 200)
        self.assertEqual(dl_res.content, file_content)

        # View file inline
        view_res = self.client.get(f"/api/v1/employee-documents/{doc_id}/view")
        self.assertEqual(view_res.status_code, 200)
        self.assertEqual(view_res.content, file_content)

    def test_update_and_delete_document(self):
        file_content = b"Tax statement 2026 content"
        upload_res = self.client.post(
            "/api/v1/employees/401/documents/upload",
            files={"file": ("tax.pdf", io.BytesIO(file_content), "application/pdf")},
            data={"file_title": "Old Tax Title", "file_category": "tax_document"},
        )
        self.assertEqual(upload_res.status_code, 201)
        doc_id = upload_res.json()["id"]

        # Update metadata
        update_res = self.client.put(
            f"/api/v1/employee-documents/{doc_id}",
            json={"file_title": "Updated Tax Statement 2026", "description": "Verified by accounts"},
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["file_title"], "Updated Tax Statement 2026")
        self.assertEqual(update_res.json()["description"], "Verified by accounts")

        # Delete document
        del_res = self.client.delete(f"/api/v1/employee-documents/{doc_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

        # Verify not found after deletion
        get_res = self.client.get(f"/api/v1/employee-documents/{doc_id}")
        self.assertEqual(get_res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
