import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from ....schemas.attendance import (
    AttendanceAuditLogListResponse,
    AttendanceChartResponse,
    AttendanceHistoryListResponse,
    AttendanceKpiResponse,
    AttendancePunchCreate,
    AttendancePunchListResponse,
    AttendanceRecordCreate,
    AttendanceRecordDeleteResponse,
    AttendanceRecordResponse,
    AttendanceRecordSingleResponse,
    AttendanceRecordUpdate,
    AttendanceSummaryResponse,
    AutoCheckoutJobResponse,
    EmployeeAttendanceDetailsResponse,
    PunchActionResponse,
    PunchDetail,
    PunchRequest,
    PunchStateResponse,
)
from ....services.attendance_service import ATTENDANCE_SERVICE
from ...deps import CurrentAuth, get_current_auth, get_db

attendance_router = APIRouter()


# ============================================================================
# 1. PUNCH OPERATIONS
# ============================================================================

@attendance_router.get(
    "/punch-state",
    response_model=PunchStateResponse,
    summary="Get current punch status for employee",
)
def get_punch_state(
    *,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
    employee_id: Optional[int] = Query(None, description="Employee ID (defaults to current user)"),
) -> PunchStateResponse:
    target_emp_id = employee_id if (employee_id is not None and auth.is_manager_or_lead) else auth.employee_id
    state_data = ATTENDANCE_SERVICE.get_punch_state(db, auth.organization_id, target_emp_id)
    return PunchStateResponse(success=True, data=state_data)


@attendance_router.post(
    "/punch",
    response_model=PunchActionResponse,
    summary="Record punch (in, out, or toggle)",
)
def record_punch(
    *,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
    payload: PunchRequest = Body(default_factory=PunchRequest),
    employee_id: Optional[int] = Query(None, description="Employee ID to punch for (if manager/admin)"),
) -> PunchActionResponse:
    target_emp_id = employee_id if (employee_id is not None and auth.is_manager_or_lead) else auth.employee_id
    state_data, message = ATTENDANCE_SERVICE.record_punch(
        db=db,
        organization_id=auth.organization_id,
        employee_id=target_emp_id,
        punch_type_req=payload.type,
        note=payload.note,
        location=payload.location,
        device_info=payload.deviceInfo,
    )
    return PunchActionResponse(success=True, message=message, data=state_data)


# ============================================================================
# 2. MY ATTENDANCE SUMMARY & TIMELINE
# ============================================================================

@attendance_router.get(
    "/summary/my",
    response_model=AttendanceSummaryResponse,
    summary="Get attendance hours summary & today timeline for current user",
)
def get_my_summary(
    *,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
    employee_id: Optional[int] = Query(None, description="Employee ID override for manager/admin"),
) -> AttendanceSummaryResponse:
    target_emp_id = employee_id if (employee_id is not None and auth.is_manager_or_lead) else auth.employee_id
    summary_data = ATTENDANCE_SERVICE.get_employee_summary(db, auth.organization_id, target_emp_id)
    return AttendanceSummaryResponse(success=True, data=summary_data)


@attendance_router.get(
    "/history/my",
    response_model=AttendanceHistoryListResponse,
    summary="Get paginated attendance history for current user",
)
def get_my_history(
    *,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
    employee_id: Optional[int] = Query(None, description="Employee ID override for manager/admin"),
    start_date: Optional[date] = Query(None, description="Filter from start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter to end date (YYYY-MM-DD)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month (1-12)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Filter by year"),
    status: Optional[str] = Query(None, description="Filter by status (Present, Absent, Half Day, Late)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    sort_by: str = Query("date", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
) -> AttendanceHistoryListResponse:
    target_emp_id = employee_id if (employee_id is not None and auth.is_manager_or_lead) else auth.employee_id
    items, pagination = ATTENDANCE_SERVICE.get_attendance_records(
        db=db,
        organization_id=auth.organization_id,
        employee_ids=[target_emp_id],
        start_date=start_date,
        end_date=end_date,
        month=month,
        year=year,
        status_filter=status,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return AttendanceHistoryListResponse(success=True, data=items, pagination=pagination)


# ============================================================================
# 3. ATTENDANCE RECORDS (ADMIN / MANAGER VIEW & CRUD)
# ============================================================================

@attendance_router.get(
    "/records",
    response_model=AttendanceHistoryListResponse,
    summary="List attendance records with filters and pagination",
)
@attendance_router.get(
    "",
    response_model=AttendanceHistoryListResponse,
    include_in_schema=False,
)
@attendance_router.get(
    "/",
    response_model=AttendanceHistoryListResponse,
    include_in_schema=False,
)
@attendance_router.get(
    "/history",
    response_model=AttendanceHistoryListResponse,
    include_in_schema=False,
)
def list_attendance_records(
    *,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
    employee_id: Optional[int] = Query(None, description="Filter by single employee ID"),
    employee_ids: Optional[List[int]] = Query(None, description="Filter by list of employee IDs"),
    date: Optional[date] = Query(None, description="Filter by exact date (YYYY-MM-DD)"),
    start_date: Optional[date] = Query(None, description="Filter from start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter to end date (YYYY-MM-DD)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month (1-12)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Filter by year"),
    status: Optional[str] = Query(None, description="Filter by status (Present, Absent, Half Day, Late)"),
    search: Optional[str] = Query(None, description="Search by employee name or email"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    sort_by: str = Query("date", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
) -> AttendanceHistoryListResponse:
    filter_emp_ids = None
    if employee_ids:
        filter_emp_ids = employee_ids
    elif employee_id is not None:
        filter_emp_ids = [employee_id]

    items, pagination = ATTENDANCE_SERVICE.get_attendance_records(
        db=db,
        organization_id=auth.organization_id,
        employee_ids=filter_emp_ids,
        date_filter=date,
        start_date=start_date,
        end_date=end_date,
        month=month,
        year=year,
        status_filter=status,
        search=search,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return AttendanceHistoryListResponse(success=True, data=items, pagination=pagination)


@attendance_router.post(
    "/records",
    response_model=AttendanceRecordSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manually create an attendance record",
)
def create_attendance_record(
    *,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
    payload: AttendanceRecordCreate = Body(...),
) -> AttendanceRecordSingleResponse:
    changed_by = auth.user.email if (auth.user and auth.user.email) else "admin"
    record = ATTENDANCE_SERVICE.create_manual_record(
        db=db,
        organization_id=auth.organization_id,
        payload=payload,
        changed_by=changed_by,
    )
    return AttendanceRecordSingleResponse(
        success=True,
        message="Attendance record created successfully",
        data=record,
    )


@attendance_router.get(
    "/records/{record_id}",
    response_model=AttendanceRecordSingleResponse,
    summary="Get single attendance record by ID",
)
def get_attendance_record(
    *,
    record_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
) -> AttendanceRecordSingleResponse:
    record = ATTENDANCE_SERVICE.get_single_record(db, auth.organization_id, record_id)
    return AttendanceRecordSingleResponse(success=True, data=record)


@attendance_router.put(
    "/records/{record_id}",
    response_model=AttendanceRecordSingleResponse,
    summary="Update attendance record (check-in, check-out, status, notes)",
)
@attendance_router.patch(
    "/records/{record_id}",
    response_model=AttendanceRecordSingleResponse,
    include_in_schema=False,
)
def update_attendance_record(
    *,
    record_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
    payload: AttendanceRecordUpdate = Body(...),
) -> AttendanceRecordSingleResponse:
    changed_by = auth.user.email if (auth.user and auth.user.email) else "admin"
    updated_record = ATTENDANCE_SERVICE.update_manual_record(
        db=db,
        organization_id=auth.organization_id,
        record_id=record_id,
        payload=payload,
        changed_by=changed_by,
    )
    return AttendanceRecordSingleResponse(
        success=True,
        message="Attendance record updated successfully",
        data=updated_record,
    )


@attendance_router.delete(
    "/records/{record_id}",
    response_model=AttendanceRecordDeleteResponse,
    summary="Delete attendance record",
)
def delete_attendance_record(
    *,
    record_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
) -> AttendanceRecordDeleteResponse:
    ATTENDANCE_SERVICE.delete_record(db, auth.organization_id, record_id)
    return AttendanceRecordDeleteResponse(
        success=True,
        message=f"Attendance record with ID '{record_id}' deleted successfully",
    )


# ============================================================================
# 4. RECORD PUNCHES SUB-RESOURCE
# ============================================================================

@attendance_router.get(
    "/records/{record_id}/punches",
    response_model=AttendancePunchListResponse,
    summary="Get all punches for an attendance record",
)
def list_record_punches(
    *,
    record_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
) -> AttendancePunchListResponse:
    punches = ATTENDANCE_SERVICE.get_record_punches(db, auth.organization_id, record_id)
    return AttendancePunchListResponse(success=True, data=punches)


@attendance_router.post(
    "/records/{record_id}/punches",
    response_model=PunchDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Add a manual punch to an attendance record",
)
def add_record_punch(
    *,
    record_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
    payload: AttendancePunchCreate = Body(...),
) -> PunchDetail:
    changed_by = auth.user.email if (auth.user and auth.user.email) else "admin"
    return ATTENDANCE_SERVICE.add_manual_punch(
        db=db,
        organization_id=auth.organization_id,
        record_id=record_id,
        payload=payload,
        changed_by=changed_by,
    )


@attendance_router.delete(
    "/punches/{punch_id}",
    response_model=AttendanceRecordDeleteResponse,
    summary="Delete punch and recalculate attendance record",
)
def delete_record_punch(
    *,
    punch_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
) -> AttendanceRecordDeleteResponse:
    changed_by = auth.user.email if (auth.user and auth.user.email) else "admin"
    ATTENDANCE_SERVICE.delete_punch(
        db=db,
        organization_id=auth.organization_id,
        punch_id=punch_id,
        changed_by=changed_by,
    )
    return AttendanceRecordDeleteResponse(
        success=True,
        message=f"Punch with ID '{punch_id}' deleted successfully",
    )


# ============================================================================
# 5. REPORTING, KPIS & ANALYTICS
# ============================================================================

@attendance_router.get(
    "/report/kpis",
    response_model=AttendanceKpiResponse,
    summary="Get attendance KPIs (supports 'average' and 'total' modes)",
)
def get_report_kpis(
    *,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
    mode: str = Query("average", description="Calculation mode: 'average' or 'total'"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Target month (1-12)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Target year"),
    department: Optional[str] = Query(None, description="Filter by department"),
) -> AttendanceKpiResponse:
    kpi_cards = ATTENDANCE_SERVICE.get_report_kpis(
        db=db,
        organization_id=auth.organization_id,
        mode=mode,
        month=month,
        year=year,
        department=department,
    )
    return AttendanceKpiResponse(success=True, data=kpi_cards)


@attendance_router.get(
    "/report/chart",
    response_model=AttendanceChartResponse,
    summary="Get 12-month chart data (Present vs Absent breakdown)",
)
def get_report_chart(
    *,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Target year"),
    department: Optional[str] = Query(None, description="Filter by department"),
) -> AttendanceChartResponse:
    bars = ATTENDANCE_SERVICE.get_report_chart(
        db=db,
        organization_id=auth.organization_id,
        year=year,
        department=department,
    )
    return AttendanceChartResponse(success=True, data=bars)


@attendance_router.get(
    "/employee/{employee_id}/details",
    response_model=EmployeeAttendanceDetailsResponse,
    summary="Get employee attendance drill-down details",
)
def get_employee_attendance_details(
    *,
    employee_id: int,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
    date: Optional[date] = Query(None, description="Target date for timeline/record"),
) -> EmployeeAttendanceDetailsResponse:
    details = ATTENDANCE_SERVICE.get_employee_details(
        db=db,
        organization_id=auth.organization_id,
        employee_id=employee_id,
        target_date=date,
    )
    return EmployeeAttendanceDetailsResponse(success=True, data=details)


# ============================================================================
# 6. CSV EXPORT
# ============================================================================

@attendance_router.get(
    "/export",
    summary="Export attendance records to CSV",
)
def export_attendance_records(
    *,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
    employee_id: Optional[int] = Query(None),
    date: Optional[date] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
) -> Response:
    filter_emp_ids = [employee_id] if employee_id is not None else None
    items, _ = ATTENDANCE_SERVICE.get_attendance_records(
        db=db,
        organization_id=auth.organization_id,
        employee_ids=filter_emp_ids,
        date_filter=date,
        start_date=start_date,
        end_date=end_date,
        month=month,
        year=year,
        status_filter=status,
        search=search,
        page=1,
        page_size=10000,
    )
    csv_content = ATTENDANCE_SERVICE.export_attendance_csv(db, auth.organization_id, items)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_export.csv"},
    )


# ============================================================================
# 7. AUTOMATION JOBS & AUDIT LOGS
# ============================================================================

@attendance_router.post(
    "/auto-checkout/run",
    response_model=AutoCheckoutJobResponse,
    summary="Trigger missing checkout policy evaluation across organization",
)
def trigger_auto_checkout_job(
    *,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
) -> AutoCheckoutJobResponse:
    processed, auto_checked = ATTENDANCE_SERVICE.run_auto_checkout_job(
        db=db,
        organization_id=auth.organization_id,
    )
    return AutoCheckoutJobResponse(
        success=True,
        message="Auto-checkout evaluation completed successfully",
        processedCount=processed,
        autoCheckedOutCount=auto_checked,
    )


@attendance_router.get(
    "/audit-logs",
    response_model=AttendanceAuditLogListResponse,
    summary="List attendance audit trail entries",
)
def list_attendance_audit_logs(
    *,
    db: Session = Depends(get_db),
    auth: CurrentAuth = Depends(get_current_auth),
    attendance_record_id: Optional[uuid.UUID] = Query(None, description="Filter by attendance record ID"),
    employee_id: Optional[int] = Query(None, description="Filter by employee ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
) -> AttendanceAuditLogListResponse:
    logs, pagination = ATTENDANCE_SERVICE.get_audit_logs(
        db=db,
        organization_id=auth.organization_id,
        attendance_record_id=attendance_record_id,
        employee_id=employee_id,
        page=page,
        page_size=page_size,
    )
    return AttendanceAuditLogListResponse(success=True, data=logs, pagination=pagination)
