import unittest
import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.organization_service.models.organization import OrganizationDb
from app.organization_service.db.base_class import Base
from app.organization_service.api.deps import get_db
from app.organization_service.api.api_v1.endpoints.organizations import organizations
from app.user_service.models.user import UsersDb


class TestOrganizationEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create an in-memory SQLite engine
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine
        )

        # Clear schemas for SQLite in-memory testing
        OrganizationDb.__table__.schema = None
        Base.metadata.create_all(bind=cls.engine)
        UsersDb.__table__.schema = None
        UsersDb.metadata.create_all(bind=cls.engine)

        cls.app = FastAPI(title="Organization Test App")
        cls.app.include_router(organizations, prefix="/organizations", tags=["Organizations"])
        cls.app.include_router(organizations, prefix="/api/v1/organizations", tags=["Organizations"])

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        cls.app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_01_create_organization(self):
        payload = {
            "name": "Acme Global",
            "email": "contact@acmeglobal.com",
            "phone": "+1-555-0199",
            "city": "New York",
            "state": "NY",
            "country": "USA",
            "postal_code": "10001",
        }
        res = self.client.post("/organizations", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["name"], "Acme Global")
        self.assertEqual(data["slug"], "acme-global")
        self.assertEqual(data["city"], "New York")
        self.assertEqual(data["status"], "active")
        self.assertIn("id", data)

        # Verify duplicate name error
        res_dup = self.client.post("/organizations", json=payload)
        self.assertEqual(res_dup.status_code, 400)
        self.assertIn("already exists", res_dup.json()["detail"])

    def test_02_list_organizations(self):
        # Create a second organization
        self.client.post(
            "/organizations",
            json={
                "name": "Beta Corp",
                "city": "San Francisco",
                "country": "USA",
            },
        )
        res = self.client.get("/organizations")
        self.assertEqual(res.status_code, 200)
        orgs = res.json()
        self.assertGreaterEqual(len(orgs), 2)

        # Search filter
        res_search = self.client.get("/organizations?search=Beta")
        self.assertEqual(res_search.status_code, 200)
        search_data = res_search.json()
        self.assertEqual(len(search_data), 1)
        self.assertEqual(search_data[0]["name"], "Beta Corp")

    def test_03_get_organization_by_id(self):
        res_list = self.client.get("/organizations")
        org_id = res_list.json()[0]["id"]

        res = self.client.get(f"/organizations/{org_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], org_id)

        # 404 on non-existent UUID
        random_id = str(uuid.uuid4())
        res_404 = self.client.get(f"/organizations/{random_id}")
        self.assertEqual(res_404.status_code, 404)

    def test_04_update_organization(self):
        res_create = self.client.post(
            "/organizations",
            json={"name": "Gamma Ltd", "city": "London"},
        )
        org_id = res_create.json()["id"]

        update_payload = {
            "city": "Manchester",
            "phone": "+44-20-7946-0958",
        }
        res_patch = self.client.patch(f"/organizations/{org_id}", json=update_payload)
        self.assertEqual(res_patch.status_code, 200)
        data = res_patch.json()
        self.assertEqual(data["city"], "Manchester")
        self.assertEqual(data["phone"], "+44-20-7946-0958")
        self.assertEqual(data["name"], "Gamma Ltd")

    def test_05_deactivate_organization(self):
        res_create = self.client.post(
            "/organizations",
            json={"name": "Delta Inc", "status": "active"},
        )
        org_id = res_create.json()["id"]

        # Deactivate
        res_del = self.client.delete(f"/organizations/{org_id}")
        self.assertEqual(res_del.status_code, 200)
        del_data = res_del.json()
        self.assertTrue(del_data["success"])
        self.assertEqual(del_data["status"], "inactive")

        # Verify status is inactive via GET
        res_get = self.client.get(f"/organizations/{org_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["status"], "inactive")

    def test_06_organization_summary(self):
        res_create = self.client.post(
            "/organizations",
            json={
                "name": "Omega Enterprise",
                "city": "Chicago",
                "country": "USA",
            },
        )
        org_id = res_create.json()["id"]

        # Add a user linked to this organization in the db
        db = self.TestingSessionLocal()
        try:
            user = UsersDb(
                id=uuid.uuid4(),
                organization_id=uuid.UUID(org_id),
                email=f"user_{uuid.uuid4().hex[:6]}@omega.com",
                country_code="US",
                status="active",
            )
            db.add(user)
            db.commit()
        finally:
            db.close()

        # Check summary endpoint
        res_summary = self.client.get(f"/organizations/{org_id}/summary")
        self.assertEqual(res_summary.status_code, 200)
        summary = res_summary.json()
        self.assertEqual(summary["name"], "Omega Enterprise")
        self.assertEqual(summary["total_users"], 1)
        self.assertEqual(summary["active_users"], 1)

    def test_07_api_v1_prefix_routes(self):
        res = self.client.get("/api/v1/organizations")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)


if __name__ == "__main__":
    unittest.main()
