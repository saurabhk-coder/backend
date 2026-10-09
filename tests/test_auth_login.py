import unittest
import uuid
import time
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth_service.models.user import UserDb
from app.role_service.models.role import RoleDb
from app.auth_service.db.base_class import Base as AuthBase
from app.role_service.db.base_class import Base as RoleBase
from app.auth_service.api import deps
from app.auth_service.api.api_v1.endpoints.auth import auth
from app.auth_service.services.securityservice import SECURITY_SERVICE
from app.auth_service.services.login_rate_limiter import LOGIN_RATE_LIMITER


class TestAuthLoginEndpoints(unittest.TestCase):
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

        # Clear schema for SQLite compatibility
        RoleDb.__table__.schema = None
        UserDb.__table__.schema = None
        RoleBase.metadata.create_all(bind=cls.engine)
        AuthBase.metadata.create_all(bind=cls.engine)

        cls.app = FastAPI(title="Auth Test App")
        cls.app.include_router(auth, prefix="/api/v1/auth", tags=["Auth"])

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        cls.app.dependency_overrides[deps.get_db] = override_get_db
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        LOGIN_RATE_LIMITER.clear()
        db = self.TestingSessionLocal()
        try:
            db.query(UserDb).delete()
            db.query(RoleDb).delete()
            db.commit()

            # Seed a Role
            self.role_id = uuid.uuid4()
            self.role = RoleDb(
                id=self.role_id,
                name="Admin",
                description="Administrator role",
                permissions_json={"all": True},
            )
            db.add(self.role)

            # Seed an active User with Role
            self.active_user_id = uuid.uuid4()
            self.password = "SecretPassword123!"
            self.hashed_password = SECURITY_SERVICE.get_password_hash(self.password)
            self.active_user = UserDb(
                id=self.active_user_id,
                email="admin@example.com",
                password_salt=self.hashed_password,
                first_name="Admin",
                last_name="User",
                country_code="+1",
                role_id=self.role_id,
                is_active="True",
                status="active",
            )
            db.add(self.active_user)

            # Seed an active User without Role
            self.no_role_user_id = uuid.uuid4()
            self.no_role_user = UserDb(
                id=self.no_role_user_id,
                email="norole@example.com",
                password_salt=self.hashed_password,
                first_name="NoRole",
                last_name="User",
                country_code="+1",
                role_id=None,
                is_active="True",
                status="active",
            )
            db.add(self.no_role_user)

            # Seed an Inactive User
            self.inactive_user_id = uuid.uuid4()
            self.inactive_user = UserDb(
                id=self.inactive_user_id,
                email="inactive@example.com",
                password_salt=self.hashed_password,
                first_name="Inactive",
                last_name="User",
                country_code="+1",
                role_id=self.role_id,
                is_active="False",
                status="inactive",
            )
            db.add(self.inactive_user)

            db.commit()
        finally:
            db.close()

    def tearDown(self):
        LOGIN_RATE_LIMITER.clear()

    def test_01_successful_login_returns_role_and_token(self):
        """Successful login should return status 200, access token, and the role name."""
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "admin@example.com", "password": self.password},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertTrue(len(data["access_token"]) > 0)
        self.assertEqual(data.get("token_type"), "bearer")
        self.assertEqual(data.get("role"), "Admin")
        self.assertEqual(data.get("role_id"), str(self.role_id))
        self.assertEqual(data.get("success"), True)
        self.assertEqual(data.get("error"), False)

    def test_02_successful_login_user_without_role(self):
        """User without assigned role should return status 200 with role=None."""
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "norole@example.com", "password": self.password},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIsNone(data.get("role"))
        self.assertIsNone(data.get("role_id"))

    def test_03_login_failure_incorrect_password_returns_401(self):
        """Incorrect password must return 401 code and proper error message."""
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "admin@example.com", "password": "WrongPassword!"},
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data.get("detail"), "Incorrect email or password")

    def test_04_login_failure_nonexistent_user_returns_401(self):
        """Non-existent email must return 401 code and proper error message."""
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "doesnotexist@example.com", "password": "AnyPassword123!"},
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data.get("detail"), "Incorrect email or password")

    def test_05_inactive_user_returns_401(self):
        """Inactive user account must return 401 code and proper message."""
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "inactive@example.com", "password": self.password},
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("inactive", data.get("detail", "").lower())

    def test_06_rate_limit_block_after_5_frequent_attempts(self):
        """If same user hits API 5 times frequently with failed attempts, block for 5 min (429)."""
        username = "admin@example.com"
        wrong_password = "WrongPassword!"

        # First 4 attempts return 401
        for i in range(4):
            res = self.client.post(
                "/api/v1/auth/login",
                data={"username": username, "password": wrong_password},
            )
            self.assertEqual(
                res.status_code,
                401,
                f"Attempt {i+1} should fail with 401",
            )

        # 5th attempt hits the threshold and triggers 5-minute block
        res_5 = self.client.post(
            "/api/v1/auth/login",
            data={"username": username, "password": wrong_password},
        )
        self.assertEqual(res_5.status_code, 401)
        self.assertIn("blocked", res_5.json().get("detail", "").lower())

        # 6th attempt within 5 minutes must be blocked with HTTP 429 Too Many Requests
        res_6 = self.client.post(
            "/api/v1/auth/login",
            data={"username": username, "password": wrong_password},
        )
        self.assertEqual(res_6.status_code, 429)
        self.assertIn("Retry-After", res_6.headers)
        self.assertIn("blocked", res_6.json().get("detail", "").lower())

        # Even if 7th attempt tries with CORRECT password, user remains blocked during the 5 minutes
        res_7 = self.client.post(
            "/api/v1/auth/login",
            data={"username": username, "password": self.password},
        )
        self.assertEqual(res_7.status_code, 429)

    def test_07_rate_limit_does_not_affect_other_users(self):
        """Blocking one user must not block a different user."""
        blocked_user = "admin@example.com"
        other_user = "norole@example.com"

        # Fail 5 times on blocked_user
        for _ in range(5):
            self.client.post(
                "/api/v1/auth/login",
                data={"username": blocked_user, "password": "WrongPassword!"},
            )

        # blocked_user is now blocked
        res_blocked = self.client.post(
            "/api/v1/auth/login",
            data={"username": blocked_user, "password": self.password},
        )
        self.assertEqual(res_blocked.status_code, 429)

        # other_user can still successfully log in
        res_other = self.client.post(
            "/api/v1/auth/login",
            data={"username": other_user, "password": self.password},
        )
        self.assertEqual(res_other.status_code, 200)

    def test_08_successful_login_resets_failure_counter(self):
        """A successful login resets the failed attempts counter."""
        username = "admin@example.com"

        # Fail 3 times
        for _ in range(3):
            res = self.client.post(
                "/api/v1/auth/login",
                data={"username": username, "password": "WrongPassword!"},
            )
            self.assertEqual(res.status_code, 401)

        # 4th attempt is successful
        res_success = self.client.post(
            "/api/v1/auth/login",
            data={"username": username, "password": self.password},
        )
        self.assertEqual(res_success.status_code, 200)

        # Counter is now reset; user can make up to 4 more mistakes without being blocked
        for _ in range(4):
            res = self.client.post(
                "/api/v1/auth/login",
                data={"username": username, "password": "WrongPassword!"},
            )
            self.assertEqual(res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
