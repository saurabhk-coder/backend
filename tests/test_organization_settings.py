import unittest
import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.organization_service.models.organization import OrganizationDb
from app.organization_service.models.organization_setting import OrganizationSettingDb
from app.organization_service.db.base_class import Base
from app.organization_service.api.deps import get_db
from app.organization_service.api.api_v1.endpoints.organization_settings import (
    organization_settings,
)
from app.organization_service.crud.crud_organization import CRUD_ORGANIZATION
from app.organization_service.schemas.organization import OrganizationCreate


class TestOrganizationSettingEndpoints(unittest.TestCase):
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

        OrganizationDb.__table__.schema = None
        OrganizationSettingDb.__table__.schema = None
        Base.metadata.create_all(bind=cls.engine)

        cls.app = FastAPI(title="Organization Settings Test App")
        cls.app.include_router(organization_settings, prefix="/api/v1", tags=["Organization Settings"])
        cls.app.include_router(organization_settings, tags=["Organization Settings"])

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        cls.app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(cls.app)

        # Create a test organization
        db = cls.TestingSessionLocal()
        try:
            cls.test_org = CRUD_ORGANIZATION.create(
                db,
                obj_in=OrganizationCreate(
                    name="Settings Test Corp",
                    email="admin@settingstest.com",
                ),
            )
            cls.org_id = str(cls.test_org.id)
        finally:
            db.close()

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_01_create_setting(self):
        # Create setting via PUT
        payload = {"setting_value": "dark"}
        res = self.client.put(
            f"/organizations/{self.org_id}/settings/theme",
            json=payload,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["setting_key"], "theme")
        self.assertEqual(data["setting_value"], "dark")
        self.assertEqual(data["organization_id"], self.org_id)

    def test_02_get_setting(self):
        res = self.client.get(f"/organizations/{self.org_id}/settings/theme")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["setting_key"], "theme")
        self.assertEqual(data["setting_value"], "dark")

        # Non-existent key
        res_404 = self.client.get(f"/organizations/{self.org_id}/settings/non_existent_key")
        self.assertEqual(res_404.status_code, 404)

    def test_03_update_setting_upsert(self):
        # Update existing setting
        res_update = self.client.put(
            f"/organizations/{self.org_id}/settings/theme",
            json={"setting_value": "light"},
        )
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.json()["setting_value"], "light")

        # Verify updated via GET
        res_get = self.client.get(f"/organizations/{self.org_id}/settings/theme")
        self.assertEqual(res_get.json()["setting_value"], "light")

    def test_04_list_settings(self):
        # Add another setting
        self.client.put(
            f"/organizations/{self.org_id}/settings/timezone",
            json={"setting_value": "UTC"},
        )

        res = self.client.get(f"/organizations/{self.org_id}/settings")
        self.assertEqual(res.status_code, 200)
        settings_list = res.json()
        self.assertGreaterEqual(len(settings_list), 2)
        keys = [s["setting_key"] for s in settings_list]
        self.assertIn("theme", keys)
        self.assertIn("timezone", keys)

    def test_05_delete_setting(self):
        # Add temporary setting to delete
        self.client.put(
            f"/organizations/{self.org_id}/settings/temp_key",
            json={"setting_value": "temp_value"},
        )

        res_del = self.client.delete(f"/organizations/{self.org_id}/settings/temp_key")
        self.assertEqual(res_del.status_code, 200)
        self.assertTrue(res_del.json()["success"])

        # Subsequent GET should return 404
        res_get = self.client.get(f"/organizations/{self.org_id}/settings/temp_key")
        self.assertEqual(res_get.status_code, 404)

    def test_06_non_existent_organization(self):
        random_org_id = str(uuid.uuid4())
        res = self.client.get(f"/organizations/{random_org_id}/settings")
        self.assertEqual(res.status_code, 404)

        res_put = self.client.put(
            f"/organizations/{random_org_id}/settings/some_key",
            json={"setting_value": "val"},
        )
        self.assertEqual(res_put.status_code, 404)

    def test_07_api_v1_prefix(self):
        res = self.client.get(f"/api/v1/organizations/{self.org_id}/settings")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)


if __name__ == "__main__":
    unittest.main()
