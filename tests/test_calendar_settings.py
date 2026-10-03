import unittest
import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.organization_service.models.organization import OrganizationDb
from app.organization_service.models.calendar_setting import (
    CalendarSettingDb,
    CalendarWeekendRuleDb,
)
from app.organization_service.db.base_class import Base
from app.organization_service.api.deps import get_db
from app.organization_service.api.api_v1.endpoints.calendar_settings import (
    calendar_settings_router,
)
from app.organization_service.crud.crud_organization import CRUD_ORGANIZATION
from app.organization_service.schemas.organization import OrganizationCreate


class TestCalendarSettingEndpoints(unittest.TestCase):
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


        cls.app = FastAPI(title="Calendar Settings Test App")
        cls.app.include_router(
            calendar_settings_router,
            prefix="/api/v1",
            tags=["Calendar Settings"],
        )
        cls.app.include_router(
            calendar_settings_router,
            tags=["Calendar Settings"],
        )

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
                    name="Global Tech Corp",
                    email="admin@globaltech.com",
                ),
            )
            cls.org_id = str(cls.test_org.id)

            # Second org for multi-tenant isolation testing
            cls.test_org_2 = CRUD_ORGANIZATION.create(
                db,
                obj_in=OrganizationCreate(
                    name="Second Tenant Corp",
                    email="admin@secondtenant.com",
                ),
            )
            cls.org_id_2 = str(cls.test_org_2.id)
        finally:
            db.close()

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_01_create_calendar_setting(self):
        """Test POST /api/v1/settings/calendar creates new configuration matching document spec."""
        payload = {
            "location": "London Office - Tech City",
            "organizationId": self.org_id,
            "fiscalYear": {
                "sameAsCalendar": True,
                "startMonth": "January",
                "endMonth": "December",
            },
            "leaveYear": {
                "sameAsCalendar": True,
                "startMonth": "January",
                "endMonth": "December",
            },
            "workSchedule": {
                "maxWorkingHoursPerDay": "08:30",
                "weekStartsOn": "Monday",
                "shiftStartTime": "09:00",
                "shiftEndTime": "17:30",
            },
            "minimumHours": {
                "fullDay": "07:30",
                "fullDayTolerance": "00:15",
                "halfDay": "04:00",
                "halfDayTolerance": "00:15",
            },
            "weekendDefinition": {
                "Sunday": {
                    "1st": True,
                    "2nd": True,
                    "3rd": True,
                    "4th": True,
                    "5th": True,
                    "last": True,
                    "alt": True,
                },
                "Saturday": {
                    "1st": True,
                    "2nd": True,
                    "3rd": True,
                    "4th": True,
                    "5th": True,
                    "last": True,
                    "alt": True,
                },
            },
        }

        res = self.client.post("/api/v1/settings/calendar", json=payload)
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertTrue(body["success"])

        data = body["data"]
        self.__class__.setting_id = data["id"]
        self.assertEqual(data["location"], "London Office - Tech City")
        # First calendar setting should default to isDefault: True
        self.assertTrue(data["isDefault"])
        self.assertEqual(data["workSchedule"]["maxWorkingHoursPerDay"], "08:30")
        self.assertEqual(data["workSchedule"]["shiftStartTime"], "09:00")
        self.assertEqual(data["workSchedule"]["shiftEndTime"], "17:30")
        self.assertEqual(data["minimumHours"]["fullDay"], "07:30")
        self.assertEqual(data["minimumHours"]["fullDayTolerance"], "00:15")

        # Weekend definition should contain all 7 days
        weekends = data["weekendDefinition"]
        self.assertIn("Sunday", weekends)
        self.assertIn("Saturday", weekends)
        self.assertIn("Monday", weekends)
        self.assertIn("Friday", weekends)
        self.assertTrue(weekends["Sunday"]["1st"])
        self.assertTrue(weekends["Sunday"]["alt"])
        self.assertTrue(weekends["Saturday"]["last"])
        self.assertFalse(weekends["Monday"]["1st"])
        self.assertFalse(weekends["Wednesday"]["alt"])

        # Verify relational rules table (hrms.calendar_weekend_rules) has 7 synced rows
        db = self.TestingSessionLocal()
        try:
            rules = (
                db.query(CalendarWeekendRuleDb)
                .filter(CalendarWeekendRuleDb.calendar_setting_id == uuid.UUID(self.setting_id))
                .all()
            )
            self.assertEqual(len(rules), 7)
            rules_by_day = {r.day_of_week: r for r in rules}
            self.assertTrue(rules_by_day["Sunday"].week_1st)
            self.assertTrue(rules_by_day["Sunday"].week_alt)
            self.assertFalse(rules_by_day["Monday"].week_1st)
        finally:
            db.close()

    def test_02_upsert_existing_calendar_setting(self):
        """Test POST /api/v1/settings/calendar updates existing setting for same location (upsert)."""
        payload = {
            "location": "London Office - Tech City",
            "organizationId": self.org_id,
            "workSchedule": {
                "maxWorkingHoursPerDay": "09:00",
                "weekStartsOn": "Monday",
                "shiftStartTime": "09:30",
                "shiftEndTime": "18:30",
            },
        }

        res = self.client.post("/api/v1/settings/calendar", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["id"], self.setting_id)
        self.assertEqual(data["workSchedule"]["shiftStartTime"], "09:30")
        self.assertEqual(data["workSchedule"]["shiftEndTime"], "18:30")

    def test_03_create_second_location_and_switch_default(self):
        """Test creating a second calendar setting and making it default."""
        payload = {
            "location": "Main HQ - Bangalore",
            "organizationId": self.org_id,
            "isDefault": True,
            "fiscalYear": {
                "sameAsCalendar": True,
                "startMonth": "January",
                "endMonth": "December",
            },
            "leaveYear": {
                "sameAsCalendar": True,
                "startMonth": "January",
                "endMonth": "December",
            },
            "workSchedule": {
                "maxWorkingHoursPerDay": "09:00",
                "weekStartsOn": "Monday",
                "shiftStartTime": "09:00",
                "shiftEndTime": "18:00",
            },
            "minimumHours": {
                "fullDay": "08:00",
                "fullDayTolerance": "00:00",
                "halfDay": "04:00",
                "halfDayTolerance": "00:00",
            },
            "weekendDefinition": {
                "Sunday": {
                    "1st": True,
                    "2nd": True,
                    "3rd": True,
                    "4th": True,
                    "5th": True,
                    "last": True,
                    "alt": True,
                },
                "Saturday": {
                    "1st": False,
                    "2nd": True,
                    "3rd": False,
                    "4th": True,
                    "5th": False,
                    "last": False,
                    "alt": False,
                },
            },
        }

        res = self.client.post("/api/v1/settings/calendar", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()["data"]
        self.__class__.setting_id_2 = data["id"]
        self.assertTrue(data["isDefault"])
        self.assertEqual(data["location"], "Main HQ - Bangalore")

        # Verify previous setting London is no longer default
        res_old = self.client.get(f"/api/v1/settings/calendar/{self.setting_id}")
        self.assertEqual(res_old.status_code, 200)
        self.assertFalse(res_old.json()["data"]["isDefault"])

    def test_04_list_calendar_settings(self):
        """Test GET /api/v1/settings/calendar lists all settings for organization."""
        res = self.client.get(
            f"/api/v1/settings/calendar?organization_id={self.org_id}"
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        items = body["data"]
        self.assertEqual(len(items), 2)
        # Default setting should be first
        self.assertTrue(items[0]["isDefault"])
        self.assertEqual(items[0]["location"], "Main HQ - Bangalore")
        self.assertFalse(items[1]["isDefault"])
        self.assertEqual(items[1]["location"], "London Office - Tech City")

    def test_05_get_setting_by_id(self):
        """Test GET /api/v1/settings/calendar/{id} by UUID."""
        res = self.client.get(f"/api/v1/settings/calendar/{self.setting_id_2}")
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["id"], self.setting_id_2)
        self.assertEqual(data["location"], "Main HQ - Bangalore")

    def test_06_get_setting_by_location(self):
        """Test GET /api/v1/settings/calendar/{location} by location name."""
        res = self.client.get(
            f"/api/v1/settings/calendar/London Office - Tech City?organization_id={self.org_id}"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["id"], self.setting_id)

    def test_07_get_setting_by_default_keyword(self):
        """Test GET /api/v1/settings/calendar/default fetches organization's default setting."""
        res = self.client.get(
            f"/api/v1/settings/calendar/default?organization_id={self.org_id}"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["id"], self.setting_id_2)
        self.assertTrue(data["isDefault"])

    def test_08_get_setting_not_found(self):
        """Test GET /api/v1/settings/calendar/{id} returns 404 for non-existent setting."""
        random_uuid = str(uuid.uuid4())
        res = self.client.get(f"/api/v1/settings/calendar/{random_uuid}")
        self.assertEqual(res.status_code, 404)

        res_loc = self.client.get("/api/v1/settings/calendar/NonExistentLocationXYZ")
        self.assertEqual(res_loc.status_code, 404)

    def test_09_update_setting_put(self):
        """Test PUT /api/v1/settings/calendar/{id} updates existing setting."""
        payload = {
            "workSchedule": {
                "maxWorkingHoursPerDay": "08:00",
                "weekStartsOn": "Sunday",
                "shiftStartTime": "08:30",
                "shiftEndTime": "16:30",
            },
            "minimumHours": {
                "fullDay": "07:00",
                "fullDayTolerance": "00:10",
                "halfDay": "03:30",
                "halfDayTolerance": "00:10",
            },
            "weekendDefinition": {
                "Friday": {
                    "1st": True,
                    "2nd": True,
                    "3rd": True,
                    "4th": True,
                    "5th": True,
                    "last": True,
                    "alt": False,
                }
            },
        }

        res = self.client.put(
            f"/api/v1/settings/calendar/{self.setting_id}",
            json=payload,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["workSchedule"]["maxWorkingHoursPerDay"], "08:00")
        self.assertEqual(data["workSchedule"]["weekStartsOn"], "Sunday")
        self.assertEqual(data["workSchedule"]["shiftStartTime"], "08:30")
        self.assertEqual(data["minimumHours"]["fullDay"], "07:00")
        self.assertTrue(data["weekendDefinition"]["Friday"]["1st"])

        # Check DB relational rule synced
        db = self.TestingSessionLocal()
        try:
            fri_rule = (
                db.query(CalendarWeekendRuleDb)
                .filter(
                    CalendarWeekendRuleDb.calendar_setting_id == uuid.UUID(self.setting_id),
                    CalendarWeekendRuleDb.day_of_week == "Friday",
                )
                .first()
            )
            self.assertIsNotNone(fri_rule)
            self.assertTrue(fri_rule.week_1st)
            self.assertFalse(fri_rule.week_alt)
        finally:
            db.close()

    def test_10_delete_setting_and_fallback_to_default(self):
        """Test DELETE /api/v1/settings/calendar/{id} removes setting and falls back to default."""
        # Delete Bangalore (current default)
        res = self.client.delete(f"/api/v1/settings/calendar/{self.setting_id_2}")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertIn("fallback to organization default", body["message"])

        # Confirm deleted setting is gone
        res_check = self.client.get(f"/api/v1/settings/calendar/{self.setting_id_2}")
        self.assertEqual(res_check.status_code, 404)

        # Remaining setting (London) should have fallen back to become default
        res_remaining = self.client.get(f"/api/v1/settings/calendar/{self.setting_id}")
        self.assertEqual(res_remaining.status_code, 200)
        self.assertTrue(res_remaining.json()["data"]["isDefault"])

    def test_11_multi_tenant_isolation(self):
        """Test that calendar settings for Tenant A are isolated from Tenant B."""
        # Create setting for second organization
        res = self.client.post(
            "/api/v1/settings/calendar",
            json={
                "location": "Tokyo Branch",
                "organizationId": self.org_id_2,
            },
        )
        self.assertEqual(res.status_code, 201)
        tokyo_id = res.json()["data"]["id"]

        # List Tenant A settings: should only contain London
        res_org1 = self.client.get(
            f"/api/v1/settings/calendar?organization_id={self.org_id}"
        )
        self.assertEqual(res_org1.status_code, 200)
        org1_locations = [x["location"] for x in res_org1.json()["data"]]
        self.assertIn("London Office - Tech City", org1_locations)
        self.assertNotIn("Tokyo Branch", org1_locations)

        # List Tenant B settings: should only contain Tokyo
        res_org2 = self.client.get(
            f"/api/v1/settings/calendar?organization_id={self.org_id_2}"
        )
        self.assertEqual(res_org2.status_code, 200)
        org2_locations = [x["location"] for x in res_org2.json()["data"]]
        self.assertIn("Tokyo Branch", org2_locations)
        self.assertNotIn("London Office - Tech City", org2_locations)


if __name__ == "__main__":
    unittest.main()
