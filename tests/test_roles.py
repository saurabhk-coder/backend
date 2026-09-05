import unittest
import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.role_service.models.role import RoleDb
from app.role_service.db.base_class import Base
from app.role_service.api.deps import get_db
from app.role_service.api.api_v1.endpoints.roles import roles
import main


class TestRoleEndpoints(unittest.TestCase):
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

        # Clear schema for SQLite compatibility in tests
        RoleDb.__table__.schema = None
        Base.metadata.create_all(bind=cls.engine)

        # Build test app
        cls.app = FastAPI(title="Test App")
        cls.app.include_router(roles, prefix="/roles", tags=["Roles"])
        cls.app.include_router(roles, prefix="/api/v1/roles", tags=["Roles"])

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

    def test_01_create_role(self):
        payload = {
            "name": "Admin",
            "description": "Administrator role with full access",
            "permissions_json": {
                "users": ["create", "read", "update", "delete"],
                "roles": ["create", "read", "update", "delete"],
            },
        }
        res = self.client.post("/roles", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["name"], "Admin")
        self.assertEqual(data["description"], "Administrator role with full access")
        self.assertIn("users", data["permissions_json"])
        self.assertIn("id", data)

        # Verify duplicate name produces 400
        res_dup = self.client.post("/roles", json=payload)
        self.assertEqual(res_dup.status_code, 400)
        self.assertIn("already exists", res_dup.json()["detail"])

    def test_02_list_roles(self):
        # Create second role
        self.client.post(
            "/roles",
            json={
                "name": "Viewer",
                "description": "Read only role",
                "permissions_json": {"users": ["read"]},
            },
        )
        res = self.client.get("/roles")
        self.assertEqual(res.status_code, 200)
        roles_list = res.json()
        self.assertGreaterEqual(len(roles_list), 2)

        # Test search filter
        res_search = self.client.get("/roles?search=Viewer")
        self.assertEqual(res_search.status_code, 200)
        search_data = res_search.json()
        self.assertEqual(len(search_data), 1)
        self.assertEqual(search_data[0]["name"], "Viewer")

    def test_03_get_role_by_id(self):
        res_list = self.client.get("/roles")
        role_id = res_list.json()[0]["id"]

        res = self.client.get(f"/roles/{role_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["id"], role_id)

        # Non-existent ID
        random_id = str(uuid.uuid4())
        res_404 = self.client.get(f"/roles/{random_id}")
        self.assertEqual(res_404.status_code, 404)

    def test_04_update_role(self):
        res_create = self.client.post(
            "/roles",
            json={
                "name": "Editor",
                "description": "Can edit content",
                "permissions_json": {"posts": ["update"]},
            },
        )
        role_id = res_create.json()["id"]

        update_payload = {
            "name": "Senior Editor",
            "description": "Can edit and publish content",
        }
        res_patch = self.client.patch(f"/roles/{role_id}", json=update_payload)
        self.assertEqual(res_patch.status_code, 200)
        data = res_patch.json()
        self.assertEqual(data["name"], "Senior Editor")
        self.assertEqual(data["description"], "Can edit and publish content")
        # Ensure permissions were preserved
        self.assertEqual(data["permissions_json"], {"posts": ["update"]})

    def test_05_get_and_replace_permissions(self):
        res_create = self.client.post(
            "/roles",
            json={
                "name": "Moderator",
                "permissions_json": ["comment:delete", "post:flag"],
            },
        )
        role_id = res_create.json()["id"]

        # GET permissions
        res_perm = self.client.get(f"/roles/{role_id}/permissions")
        self.assertEqual(res_perm.status_code, 200)
        self.assertEqual(res_perm.json()["permissions"], ["comment:delete", "post:flag"])

        # PUT permissions (replace) with structured object
        new_perms = {"users": ["read", "suspend"], "audit": ["read"]}
        res_put = self.client.put(
            f"/roles/{role_id}/permissions",
            json={"permissions": new_perms},
        )
        self.assertEqual(res_put.status_code, 200)
        self.assertEqual(res_put.json()["permissions"], new_perms)

        # PUT permissions (replace) with direct list
        list_perms = ["perm:a", "perm:b"]
        res_put_list = self.client.put(
            f"/roles/{role_id}/permissions",
            json=list_perms,
        )
        self.assertEqual(res_put_list.status_code, 200)
        self.assertEqual(res_put_list.json()["permissions"], list_perms)

    def test_06_delete_role(self):
        res_create = self.client.post(
            "/roles",
            json={"name": "TempRole", "description": "To be deleted"},
        )
        role_id = res_create.json()["id"]

        # Delete role
        res_del = self.client.delete(f"/roles/{role_id}")
        self.assertEqual(res_del.status_code, 200)
        self.assertTrue(res_del.json()["success"])

        # Verify not found afterwards
        res_get = self.client.get(f"/roles/{role_id}")
        self.assertEqual(res_get.status_code, 404)

    def test_07_api_v1_prefix_routes(self):
        # Verify /api/v1/roles prefix works identically
        res = self.client.get("/api/v1/roles")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)


if __name__ == "__main__":
    unittest.main()
