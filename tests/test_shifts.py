import unittest
import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.organization_service.models.organization import OrganizationDb
from app.shift_service.models.shift import (
    ShiftDb,
    ShiftGracePeriodDb,
    ShiftReminderDb,
)
from app.shift_service.db.base_class import Base
from app.shift_service.api.deps import get_db
from app.shift_service.api.api_v1.endpoints.shifts import shifts
from app.organization_service.crud.crud_organization import CRUD_ORGANIZATION
from app.organization_service.schemas.organization import OrganizationCreate


class TestShiftEndpoints(unittest.TestCase):
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


        cls.app = FastAPI(title="Shifts Test App")
        cls.app.include_router(shifts, prefix="/api/v1/shifts", tags=["Shifts"])
        cls.app.include_router(shifts, prefix="/shifts", tags=["Shifts"])

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        cls.app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(cls.app)

        # Create two test organizations for multi-tenancy tests
        db = cls.TestingSessionLocal()
        try:
            cls.test_org_1 = CRUD_ORGANIZATION.create(
                db,
                obj_in=OrganizationCreate(
                    name="Shift Tech Corp",
                    email="admin@shiftcorp.com",
                ),
            )
            cls.org_id_1 = str(cls.test_org_1.id)

            cls.test_org_2 = CRUD_ORGANIZATION.create(
                db,
                obj_in=OrganizationCreate(
                    name="Second Shift Corp",
                    email="admin@secondshift.com",
                ),
            )
            cls.org_id_2 = str(cls.test_org_2.id)
        finally:
            db.close()

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_01_create_shift(self):
        """Test POST /api/v1/shifts matching the document request body exactly."""
        payload = {
            "name": "General Morning Shift",
            "startTime": "09:00",
            "endTime": "18:00",
            "shiftDuration": "09:00",
            "startDate": "2026-01-01",
            "endDate": "2026-12-31",
            "peopleRequired": "10-20 People",
            "color": "#F05A28",
            "workArea": "Main HQ - Floor 3",
            "department": "Engineering",
            "location": "Bangalore",
            "payCalculationType": "per_day",
            "minimumHours": {
                "fullDay": "08:00",
                "fullDayTolerance": "00:30",
                "halfDay": "04:30",
                "halfDayTolerance": "00:15",
            },
            "recurrencePattern": "daily",
            "weeklyDays": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "calendarWeekendPolicy": "calendar",
            "gracePeriodPolicy": {
                "enabled": True,
                "lateCheckInMinutes": 15,
                "earlyCheckOutMinutes": 10,
            },
            "shiftReminder": {
                "checkIn": {
                    "enabled": True,
                    "beforeTime": "00:15",
                    "afterTime": "00:10",
                },
                "checkOut": {
                    "enabled": True,
                    "beforeTime": "00:10",
                    "afterTime": "00:15",
                },
            },
            "organizationId": self.org_id_1,
        }

        res = self.client.post("/api/v1/shifts", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.__class__.shift_id = data["id"]

        self.assertEqual(data["name"], "General Morning Shift")
        self.assertEqual(data["startTime"], "09:00")
        self.assertEqual(data["endTime"], "18:00")
        self.assertEqual(data["shiftDuration"], "09:00")
        self.assertEqual(data["department"], "Engineering")
        self.assertEqual(data["location"], "Bangalore")
        self.assertEqual(data["color"], "#F05A28")
        self.assertEqual(data["minimumHours"]["fullDay"], "08:00")
        self.assertEqual(data["minimumHours"]["fullDayTolerance"], "00:30")
        self.assertEqual(data["minimumHours"]["halfDay"], "04:30")
        self.assertEqual(data["minimumHours"]["halfDayTolerance"], "00:15")
        self.assertTrue(data["gracePeriodPolicy"]["enabled"])
        self.assertEqual(data["gracePeriodPolicy"]["lateCheckInMinutes"], 15)
        self.assertEqual(data["gracePeriodPolicy"]["earlyCheckOutMinutes"], 10)
        self.assertTrue(data["shiftReminder"]["checkIn"]["enabled"])
        self.assertEqual(data["shiftReminder"]["checkIn"]["beforeTime"], "00:15")
        self.assertEqual(data["shiftReminder"]["checkOut"]["afterTime"], "00:15")
        self.assertTrue(data["isActive"])
        self.assertIsNotNone(data["createdAt"])
        self.assertIsNotNone(data["updatedAt"])

    def test_02_get_shift_by_id(self):
        """Test GET /api/v1/shifts/{id}."""
        res = self.client.get(f"/api/v1/shifts/{self.shift_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["id"], self.shift_id)
        self.assertEqual(data["name"], "General Morning Shift")

    def test_03_list_shifts(self):
        """Test GET /api/v1/shifts with pagination structure."""
        res = self.client.get(
            f"/api/v1/shifts?organization_id={self.org_id_1}&page=1&page_size=20"
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(len(body["data"]), 1)
        self.assertEqual(body["data"][0]["id"], self.shift_id)

        pag = body["pagination"]
        self.assertEqual(pag["page"], 1)
        self.assertEqual(pag["pageSize"], 20)
        self.assertEqual(pag["total"], 1)
        self.assertEqual(pag["totalPages"], 1)

    def test_04_list_shifts_filters(self):
        """Test filters: search, department, location, is_active."""
        # Search match
        res_search = self.client.get(
            f"/api/v1/shifts?organization_id={self.org_id_1}&search=Morning"
        )
        self.assertEqual(res_search.status_code, 200)
        self.assertEqual(len(res_search.json()["data"]), 1)

        # Search no match
        res_no = self.client.get(
            f"/api/v1/shifts?organization_id={self.org_id_1}&search=NightShiftXYZ"
        )
        self.assertEqual(res_no.status_code, 200)
        self.assertEqual(len(res_no.json()["data"]), 0)

        # Department filter
        res_dept = self.client.get(
            f"/api/v1/shifts?organization_id={self.org_id_1}&department=Engineering"
        )
        self.assertEqual(res_dept.status_code, 200)
        self.assertEqual(len(res_dept.json()["data"]), 1)

        # Location filter
        res_loc = self.client.get(
            f"/api/v1/shifts?organization_id={self.org_id_1}&location=Bangalore"
        )
        self.assertEqual(res_loc.status_code, 200)
        self.assertEqual(len(res_loc.json()["data"]), 1)

    def test_05_update_shift(self):
        """Test PUT /api/v1/shifts/{id}."""
        payload = {
            "name": "Updated Morning Shift",
            "startTime": "08:30",
            "endTime": "17:30",
            "color": "#3B82F6",
            "gracePeriodPolicy": {
                "enabled": True,
                "lateCheckInMinutes": 20,
                "earlyCheckOutMinutes": 15,
            },
        }

        res = self.client.put(f"/api/v1/shifts/{self.shift_id}", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["name"], "Updated Morning Shift")
        self.assertEqual(data["startTime"], "08:30")
        self.assertEqual(data["endTime"], "17:30")
        self.assertEqual(data["color"], "#3B82F6")
        self.assertEqual(data["gracePeriodPolicy"]["lateCheckInMinutes"], 20)
        self.assertEqual(data["gracePeriodPolicy"]["earlyCheckOutMinutes"], 15)

    def test_06_delete_shift(self):
        """Test DELETE /api/v1/shifts/{id}."""
        res = self.client.delete(f"/api/v1/shifts/{self.shift_id}")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["message"], "Shift deleted successfully")

        # Confirm 404 on get
        res_get = self.client.get(f"/api/v1/shifts/{self.shift_id}")
        self.assertEqual(res_get.status_code, 404)

    def test_07_multi_tenant_isolation(self):
        """Verify shifts created in Org 1 cannot be seen by Org 2."""
        # Create in Org 2
        res2 = self.client.post(
            "/api/v1/shifts",
            json={
                "name": "Org 2 Night Shift",
                "startTime": "20:00",
                "endTime": "05:00",
                "organizationId": self.org_id_2,
            },
        )
        self.assertEqual(res2.status_code, 201)
        shift2_id = res2.json()["id"]

        # Org 1 list should not see Org 2's shift
        res_org1 = self.client.get(f"/api/v1/shifts?organization_id={self.org_id_1}")
        self.assertEqual(res_org1.status_code, 200)
        ids_org1 = [s["id"] for s in res_org1.json()["data"]]
        self.assertNotIn(shift2_id, ids_org1)

        # Org 2 list should see Org 2's shift
        res_org2 = self.client.get(f"/api/v1/shifts?organization_id={self.org_id_2}")
        self.assertEqual(res_org2.status_code, 200)
        ids_org2 = [s["id"] for s in res_org2.json()["data"]]
        self.assertIn(shift2_id, ids_org2)


if __name__ == "__main__":
    unittest.main()
