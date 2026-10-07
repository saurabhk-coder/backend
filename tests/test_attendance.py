import unittest
import uuid
from datetime import date, datetime, timedelta, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.organization_service.db.base_class import Base
from app.organization_service.models.organization import OrganizationDb
from app.organization_service.models.organization_setting import OrganizationSettingDb
from app.employee_service.models.employee import EmployeeDb
from app.employee_service.models.employee_personal_information import EmployeePersonalInformationDb
from app.shift_service.models.shift import ShiftDb
from app.attendance_service.models.attendance import (
    AttendanceAuditLogDb,
    AttendanceMonthlyStatsDb,
    AttendancePunchDb,
    AttendanceRecordDb,
)
from app.attendance_service.api.deps import CurrentAuth, get_current_auth, get_db
from app.attendance_service.api.api_v1.endpoints.attendance import attendance_router
from app.user_service.models.user import UsersDb


class TestAttendanceEndpoints(unittest.TestCase):
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

        UsersDb.__table__.schema = None
        UsersDb.metadata.create_all(bind=cls.engine)

        cls.app = FastAPI(title="Attendance Test App")
        cls.app.include_router(attendance_router, prefix="/api/v1/attendance", tags=["Attendance"])
        cls.app.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        cls.app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(cls.app)

        # Seed Organization 1 and Employee 1
        db = cls.TestingSessionLocal()
        cls.org1_id = uuid.uuid4()
        cls.org2_id = uuid.uuid4()

        org1 = OrganizationDb(id=cls.org1_id, name="Attendance Corp")
        org2 = OrganizationDb(id=cls.org2_id, name="Other Org")
        db.add(org1)
        db.add(org2)

        emp1 = EmployeeDb(id=101, employee_code="EMP-101")
        emp2 = EmployeeDb(id=102, employee_code="EMP-102")
        db.add(emp1)
        db.add(emp2)

        emp1_info = EmployeePersonalInformationDb(
            organization_id=cls.org1_id,
            employee_id=101,
            first_name="Alice",
            last_name="Smith",
            email="alice@attendance.corp",
        )
        emp2_info = EmployeePersonalInformationDb(
            organization_id=cls.org2_id,
            employee_id=102,
            first_name="Bob",
            last_name="Jones",
            email="bob@other.org",
        )
        db.add(emp1_info)
        db.add(emp2_info)

        user1 = UsersDb(
            id=uuid.uuid4(),
            organization_id=cls.org1_id,
            email="alice@attendance.corp",
            first_name="Alice",
            last_name="Smith",
        )
        db.add(user1)

        # Seed shift for org1
        cls.shift1_id = uuid.uuid4()
        shift1 = ShiftDb(
            id=cls.shift1_id,
            organization_id=cls.org1_id,
            name="General Day Shift",
            start_time=datetime.strptime("09:00", "%H:%M").time(),
            end_time=datetime.strptime("18:00", "%H:%M").time(),
            shift_duration="09:00",
            is_active=True,
        )
        db.add(shift1)

        # Seed policy
        setting1 = OrganizationSettingDb(
            organization_id=cls.org1_id,
            setting_key="missingCheckoutPolicy",
            setting_value="auto_checkout_at_shift_end",
        )
        setting2 = OrganizationSettingDb(
            organization_id=cls.org1_id,
            setting_key="missingCheckoutGraceHours",
            setting_value="2",
        )
        db.add(setting1)
        db.add(setting2)

        db.commit()
        db.close()

    def test_01_punch_toggle_and_state(self):
        headers = {"X-Organization-Id": str(self.org1_id)}

        # Initial state: should not be punched in
        res = self.client.get("/api/v1/attendance/punch-state", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertFalse(data["isPunchedIn"])

        # Punch IN
        punch_res = self.client.post(
            "/api/v1/attendance/punch",
            json={"type": "in", "note": "Arrived at office", "location": "HQ Gate 1"},
            headers=headers,
        )
        self.assertEqual(punch_res.status_code, 200)
        punch_data = punch_res.json()["data"]
        self.assertTrue(punch_data["isPunchedIn"])
        self.assertIn("punched in", punch_res.json()["message"].lower())

        # Verify punch state
        res2 = self.client.get("/api/v1/attendance/punch-state", headers=headers)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()["data"]
        self.assertTrue(data2["isPunchedIn"])
        self.assertEqual(data2["punchesCount"], 1)

        # Punch OUT via toggle
        toggle_res = self.client.post(
            "/api/v1/attendance/punch",
            json={"type": "toggle", "note": "Going home"},
            headers=headers,
        )
        self.assertEqual(toggle_res.status_code, 200)
        toggle_data = toggle_res.json()["data"]
        self.assertFalse(toggle_data["isPunchedIn"])
        self.assertEqual(toggle_data["punchesCount"], 2)

    def test_02_summary_my_and_timeline(self):
        headers = {"X-Organization-Id": str(self.org1_id)}
        res = self.client.get("/api/v1/attendance/summary/my", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertIn("todayWorkHours", data)
        self.assertIn("weeklyWorkHours", data)
        self.assertIn("todayTimeline", data)
        self.assertIn("sessions", data)
        self.assertGreaterEqual(len(data["todayTimeline"]), 2)
        self.assertGreaterEqual(len(data["sessions"]), 1)

    def test_03_my_history(self):
        headers = {"X-Organization-Id": str(self.org1_id)}
        res = self.client.get("/api/v1/attendance/history/my", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIsInstance(data["data"], list)
        self.assertGreaterEqual(len(data["data"]), 1)
        self.assertEqual(data["pagination"]["page"], 1)

    def test_04_list_records_and_filters(self):
        headers = {"X-Organization-Id": str(self.org1_id)}
        res = self.client.get("/api/v1/attendance/records", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["data"]), 1)

        # Filter by employee_id
        res_emp = self.client.get("/api/v1/attendance/records?employee_id=101", headers=headers)
        self.assertEqual(res_emp.status_code, 200)
        self.assertTrue(all(r["employeeId"] == 101 for r in res_emp.json()["data"]))

    def test_05_manual_record_crud(self):
        headers = {"X-Organization-Id": str(self.org1_id)}
        target_date = date.today() - timedelta(days=2)

        # Create record
        create_payload = {
            "employeeId": 101,
            "date": target_date.isoformat(),
            "checkIn": f"{target_date.isoformat()}T09:00:00Z",
            "checkOut": f"{target_date.isoformat()}T18:00:00Z",
            "status": "Present",
            "notes": "Manual record for testing",
            "reason": "System sync issue",
        }
        res_create = self.client.post(
            "/api/v1/attendance/records",
            json=create_payload,
            headers=headers,
        )
        self.assertEqual(res_create.status_code, 201)
        rec_data = res_create.json()["data"]
        rec_id = rec_data["id"]
        self.assertEqual(rec_data["employeeId"], 101)
        self.assertEqual(rec_data["status"], "Present")

        # Get single record
        res_get = self.client.get(f"/api/v1/attendance/records/{rec_id}", headers=headers)
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["data"]["id"], rec_id)

        # Update record
        update_payload = {
            "status": "Half Day",
            "notes": "Updated note",
            "reason": "Left early for appointment",
        }
        res_update = self.client.put(
            f"/api/v1/attendance/records/{rec_id}",
            json=update_payload,
            headers=headers,
        )
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.json()["data"]["status"], "Half Day")

        # Delete record
        res_del = self.client.delete(f"/api/v1/attendance/records/{rec_id}", headers=headers)
        self.assertEqual(res_del.status_code, 200)

        # Verify not found after delete
        res_after = self.client.get(f"/api/v1/attendance/records/{rec_id}", headers=headers)
        self.assertEqual(res_after.status_code, 404)

    def test_06_punches_subresource(self):
        headers = {"X-Organization-Id": str(self.org1_id)}
        target_date = date.today() - timedelta(days=5)

        # Create record
        create_res = self.client.post(
            "/api/v1/attendance/records",
            json={
                "employeeId": 101,
                "date": target_date.isoformat(),
                "status": "Absent",
            },
            headers=headers,
        )
        self.assertEqual(create_res.status_code, 201)
        rec_id = create_res.json()["data"]["id"]

        # Add manual punch
        add_punch_res = self.client.post(
            f"/api/v1/attendance/records/{rec_id}/punches",
            json={
                "punchType": "IN",
                "punchTime": f"{target_date.isoformat()}T09:15:00Z",
                "location": "Front Door",
                "note": "Biometric terminal punch",
            },
            headers=headers,
        )
        self.assertEqual(add_punch_res.status_code, 201)
        punch_id = add_punch_res.json()["id"]

        # List punches
        list_punches_res = self.client.get(
            f"/api/v1/attendance/records/{rec_id}/punches",
            headers=headers,
        )
        self.assertEqual(list_punches_res.status_code, 200)
        self.assertEqual(len(list_punches_res.json()["data"]), 1)

        # Delete punch
        del_punch_res = self.client.delete(
            f"/api/v1/attendance/punches/{punch_id}",
            headers=headers,
        )
        self.assertEqual(del_punch_res.status_code, 200)

    def test_07_report_kpis_and_charts(self):
        headers = {"X-Organization-Id": str(self.org1_id)}

        # KPI average mode
        kpi_avg = self.client.get("/api/v1/attendance/report/kpis?mode=average", headers=headers)
        self.assertEqual(kpi_avg.status_code, 200)
        data = kpi_avg.json()["data"]
        self.assertIn("present", data)
        self.assertIn("absent", data)
        self.assertIn("late", data)
        self.assertIn("halfDay", data)

        # KPI total mode
        kpi_tot = self.client.get("/api/v1/attendance/report/kpis?mode=total", headers=headers)
        self.assertEqual(kpi_tot.status_code, 200)

        # Chart 12 months
        chart_res = self.client.get("/api/v1/attendance/report/chart", headers=headers)
        self.assertEqual(chart_res.status_code, 200)
        bars = chart_res.json()["data"]
        self.assertEqual(len(bars), 12)
        self.assertEqual(bars[0]["month"], "Jan")

    def test_08_employee_drill_down_details(self):
        headers = {"X-Organization-Id": str(self.org1_id)}
        res = self.client.get("/api/v1/attendance/employee/101/details", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertIn("employee", data)
        self.assertIn("kpis", data)
        self.assertIn("timeline", data)
        self.assertEqual(data["employee"]["id"], 101)

    def test_09_csv_export(self):
        headers = {"X-Organization-Id": str(self.org1_id)}
        res = self.client.get("/api/v1/attendance/export", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res.headers.get("content-type", ""))
        self.assertIn("Employee ID,Employee Code,Employee Name", res.text)

    def test_10_auto_checkout_job(self):
        headers = {"X-Organization-Id": str(self.org1_id)}
        res = self.client.post("/api/v1/attendance/auto-checkout/run", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("processedCount", data)
        self.assertIn("autoCheckedOutCount", data)

    def test_11_audit_logs(self):
        headers = {"X-Organization-Id": str(self.org1_id)}
        res = self.client.get("/api/v1/attendance/audit-logs", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIsInstance(data["data"], list)

    def test_12_multi_tenancy_isolation(self):
        # Org 2 requests should not return Org 1's records
        res_org2 = self.client.get(
            "/api/v1/attendance/records",
            headers={"X-Organization-Id": str(self.org2_id)},
        )
        self.assertEqual(res_org2.status_code, 200)
        records = res_org2.json()["data"]
        # Ensure no records belong to employee 101 of Org 1
        self.assertTrue(all(r["employeeId"] != 101 for r in records))


if __name__ == "__main__":
    unittest.main()
