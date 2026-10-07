import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PaginationInfo(BaseModel):
    page: int = 1
    pageSize: int = Field(20, validation_alias=AliasChoices("pageSize", "page_size"), serialization_alias="pageSize")
    total: int = 0
    totalPages: int = Field(1, validation_alias=AliasChoices("totalPages", "total_pages"), serialization_alias="totalPages")

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# PUNCH SCHEMAS
# ============================================================================

class PunchRequest(BaseModel):
    type: Optional[str] = Field("toggle", description="Punch type: 'in', 'out', or 'toggle'")
    note: Optional[str] = None
    location: Optional[str] = None
    deviceInfo: Optional[str] = Field(None, validation_alias=AliasChoices("deviceInfo", "device_info"), serialization_alias="deviceInfo")

    model_config = ConfigDict(populate_by_name=True)


class PunchDetail(BaseModel):
    id: uuid.UUID
    punchTime: datetime = Field(..., validation_alias=AliasChoices("punchTime", "punch_time"), serialization_alias="punchTime")
    punchType: str = Field(..., validation_alias=AliasChoices("punchType", "punch_type"), serialization_alias="punchType")
    location: Optional[str] = None
    note: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class PunchStateData(BaseModel):
    isPunchedIn: bool = Field(..., validation_alias=AliasChoices("isPunchedIn", "is_punched_in"), serialization_alias="isPunchedIn")
    date: date
    firstCheckIn: Optional[datetime] = Field(None, validation_alias=AliasChoices("firstCheckIn", "first_check_in"), serialization_alias="firstCheckIn")
    lastCheckOut: Optional[datetime] = Field(None, validation_alias=AliasChoices("lastCheckOut", "last_check_out"), serialization_alias="lastCheckOut")
    currentSessionMinutes: int = Field(0, validation_alias=AliasChoices("currentSessionMinutes", "current_session_minutes"), serialization_alias="currentSessionMinutes")
    totalWorkMinutes: int = Field(0, validation_alias=AliasChoices("totalWorkMinutes", "total_work_minutes"), serialization_alias="totalWorkMinutes")
    totalWorkHours: float = Field(0.0, validation_alias=AliasChoices("totalWorkHours", "total_work_hours"), serialization_alias="totalWorkHours")
    breakMinutes: int = Field(0, validation_alias=AliasChoices("breakMinutes", "break_minutes"), serialization_alias="breakMinutes")
    status: str = "Absent"
    punchesCount: int = Field(0, validation_alias=AliasChoices("punchesCount", "punches_count"), serialization_alias="punchesCount")
    productionIndicator: str = Field("neutral", validation_alias=AliasChoices("productionIndicator", "production_indicator"), serialization_alias="productionIndicator")
    shiftInfo: Optional[Dict[str, Any]] = Field(None, validation_alias=AliasChoices("shiftInfo", "shift_info"), serialization_alias="shiftInfo")

    model_config = ConfigDict(populate_by_name=True)


class PunchStateResponse(BaseModel):
    success: bool = True
    data: PunchStateData

    model_config = ConfigDict(populate_by_name=True)


class PunchActionResponse(BaseModel):
    success: bool = True
    message: str
    data: PunchStateData

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# SUMMARY & TIMELINE
# ============================================================================

class TimelineEvent(BaseModel):
    id: uuid.UUID
    time: datetime
    punchType: str = Field(..., validation_alias=AliasChoices("punchType", "punch_type"), serialization_alias="punchType")
    note: Optional[str] = None
    location: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class TimelineSession(BaseModel):
    sessionNumber: int = Field(..., validation_alias=AliasChoices("sessionNumber", "session_number"), serialization_alias="sessionNumber")
    checkIn: datetime = Field(..., validation_alias=AliasChoices("checkIn", "check_in"), serialization_alias="checkIn")
    checkOut: Optional[datetime] = Field(None, validation_alias=AliasChoices("checkOut", "check_out"), serialization_alias="checkOut")
    durationMinutes: int = Field(0, validation_alias=AliasChoices("durationMinutes", "duration_minutes"), serialization_alias="durationMinutes")
    durationHours: float = Field(0.0, validation_alias=AliasChoices("durationHours", "duration_hours"), serialization_alias="durationHours")

    model_config = ConfigDict(populate_by_name=True)


class AttendanceSummaryData(BaseModel):
    todayWorkHours: float = Field(0.0, validation_alias=AliasChoices("todayWorkHours", "today_work_hours"), serialization_alias="todayWorkHours")
    weeklyWorkHours: float = Field(0.0, validation_alias=AliasChoices("weeklyWorkHours", "weekly_work_hours"), serialization_alias="weeklyWorkHours")
    monthlyWorkHours: float = Field(0.0, validation_alias=AliasChoices("monthlyWorkHours", "monthly_work_hours"), serialization_alias="monthlyWorkHours")
    overtimeHours: float = Field(0.0, validation_alias=AliasChoices("overtimeHours", "overtime_hours"), serialization_alias="overtimeHours")
    todayTimeline: List[TimelineEvent] = Field(default_factory=list, validation_alias=AliasChoices("todayTimeline", "today_timeline"), serialization_alias="todayTimeline")
    sessions: List[TimelineSession] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class AttendanceSummaryResponse(BaseModel):
    success: bool = True
    data: AttendanceSummaryData

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# ATTENDANCE RECORD & HISTORY TABLE
# ============================================================================

class AttendanceRecordResponse(BaseModel):
    id: uuid.UUID
    employeeId: int = Field(..., validation_alias=AliasChoices("employeeId", "employee_id"), serialization_alias="employeeId")
    employeeName: Optional[str] = Field(None, validation_alias=AliasChoices("employeeName", "employee_name"), serialization_alias="employeeName")
    employeeCode: Optional[str] = Field(None, validation_alias=AliasChoices("employeeCode", "employee_code"), serialization_alias="employeeCode")
    department: Optional[str] = None
    designation: Optional[str] = None
    avatar: Optional[str] = None
    date: date
    checkIn: Optional[datetime] = Field(None, validation_alias=AliasChoices("checkIn", "check_in"), serialization_alias="checkIn")
    checkOut: Optional[datetime] = Field(None, validation_alias=AliasChoices("checkOut", "check_out"), serialization_alias="checkOut")
    totalWorkMinutes: int = Field(0, validation_alias=AliasChoices("totalWorkMinutes", "total_work_minutes"), serialization_alias="totalWorkMinutes")
    breakMinutes: int = Field(0, validation_alias=AliasChoices("breakMinutes", "break_minutes"), serialization_alias="breakMinutes")
    productionHours: float = Field(0.0, validation_alias=AliasChoices("productionHours", "production_hours"), serialization_alias="productionHours")
    overtimeHours: float = Field(0.0, validation_alias=AliasChoices("overtimeHours", "overtime_hours"), serialization_alias="overtimeHours")
    lateMinutes: int = Field(0, validation_alias=AliasChoices("lateMinutes", "late_minutes"), serialization_alias="lateMinutes")
    earlyLeaveMinutes: int = Field(0, validation_alias=AliasChoices("earlyLeaveMinutes", "early_leave_minutes"), serialization_alias="earlyLeaveMinutes")
    status: str = "Absent"
    autoCheckedOut: bool = Field(False, validation_alias=AliasChoices("autoCheckedOut", "auto_checked_out"), serialization_alias="autoCheckedOut")
    productionIndicator: str = Field("neutral", validation_alias=AliasChoices("productionIndicator", "production_indicator"), serialization_alias="productionIndicator")
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class AttendanceHistoryListResponse(BaseModel):
    success: bool = True
    data: List[AttendanceRecordResponse] = []
    pagination: PaginationInfo

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# ADMIN REPORT KPIS & CHARTS
# ============================================================================

class KpiCardData(BaseModel):
    title: str
    total: float
    average: float
    count: float
    delta: float = 0.0
    unit: str = "days"
    trend: str = "neutral"  # up, down, neutral

    model_config = ConfigDict(populate_by_name=True)


class AttendanceKpiResponse(BaseModel):
    success: bool = True
    data: Dict[str, KpiCardData]

    model_config = ConfigDict(populate_by_name=True)


class MonthlyChartBar(BaseModel):
    month: str
    monthIndex: int = Field(..., validation_alias=AliasChoices("monthIndex", "month_index"), serialization_alias="monthIndex")
    present: int = 0
    absent: int = 0
    halfDay: int = Field(0, validation_alias=AliasChoices("halfDay", "half_day"), serialization_alias="halfDay")
    late: int = 0
    totalEmployees: int = Field(0, validation_alias=AliasChoices("totalEmployees", "total_employees"), serialization_alias="totalEmployees")

    model_config = ConfigDict(populate_by_name=True)


class AttendanceChartResponse(BaseModel):
    success: bool = True
    data: List[MonthlyChartBar]

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# DRILL-DOWN DETAILS
# ============================================================================

class EmployeeAttendanceDetailsData(BaseModel):
    employee: Dict[str, Any]
    kpis: Dict[str, Any]
    timeline: List[TimelineEvent] = []
    todayRecord: Optional[AttendanceRecordResponse] = None

    model_config = ConfigDict(populate_by_name=True)


class EmployeeAttendanceDetailsResponse(BaseModel):
    success: bool = True
    data: EmployeeAttendanceDetailsData

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# RECORD CRUD SCHEMAS
# ============================================================================

class AttendanceRecordCreate(BaseModel):
    employeeId: int = Field(..., validation_alias=AliasChoices("employeeId", "employee_id"), serialization_alias="employeeId")
    date: date
    shiftId: Optional[uuid.UUID] = Field(None, validation_alias=AliasChoices("shiftId", "shift_id"), serialization_alias="shiftId")
    checkIn: Optional[datetime] = Field(None, validation_alias=AliasChoices("checkIn", "check_in"), serialization_alias="checkIn")
    checkOut: Optional[datetime] = Field(None, validation_alias=AliasChoices("checkOut", "check_out"), serialization_alias="checkOut")
    status: Optional[str] = "Present"
    notes: Optional[str] = None
    reason: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class AttendanceRecordUpdate(BaseModel):
    checkIn: Optional[datetime] = Field(None, validation_alias=AliasChoices("checkIn", "check_in"), serialization_alias="checkIn")
    checkOut: Optional[datetime] = Field(None, validation_alias=AliasChoices("checkOut", "check_out"), serialization_alias="checkOut")
    status: Optional[str] = None
    notes: Optional[str] = None
    reason: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class AttendanceRecordSingleResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: AttendanceRecordResponse

    model_config = ConfigDict(populate_by_name=True)


class AttendanceRecordDeleteResponse(BaseModel):
    success: bool = True
    message: str

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# MANUAL PUNCH SCHEMAS
# ============================================================================

class AttendancePunchCreate(BaseModel):
    punchTime: Optional[datetime] = Field(None, validation_alias=AliasChoices("punchTime", "punch_time"), serialization_alias="punchTime")
    punchType: str = Field(..., validation_alias=AliasChoices("punchType", "punch_type"), serialization_alias="punchType")
    location: Optional[str] = None
    deviceInfo: Optional[str] = Field(None, validation_alias=AliasChoices("deviceInfo", "device_info"), serialization_alias="deviceInfo")
    note: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class AttendancePunchListResponse(BaseModel):
    success: bool = True
    data: List[PunchDetail] = []

    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# AUDIT LOG & AUTOMATION SCHEMAS
# ============================================================================

class AttendanceAuditLogEntry(BaseModel):
    id: uuid.UUID
    attendanceRecordId: Optional[uuid.UUID] = Field(None, validation_alias=AliasChoices("attendanceRecordId", "attendance_record_id"), serialization_alias="attendanceRecordId")
    employeeId: int = Field(..., validation_alias=AliasChoices("employeeId", "employee_id"), serialization_alias="employeeId")
    action: str
    oldValues: Dict[str, Any] = Field(default_factory=dict, validation_alias=AliasChoices("oldValues", "old_values"), serialization_alias="oldValues")
    newValues: Dict[str, Any] = Field(default_factory=dict, validation_alias=AliasChoices("newValues", "new_values"), serialization_alias="newValues")
    reason: Optional[str] = None
    changedBy: str = Field("system", validation_alias=AliasChoices("changedBy", "changed_by"), serialization_alias="changedBy")
    changedAt: datetime = Field(..., validation_alias=AliasChoices("changedAt", "changed_at"), serialization_alias="changedAt")

    model_config = ConfigDict(populate_by_name=True)


class AttendanceAuditLogListResponse(BaseModel):
    success: bool = True
    data: List[AttendanceAuditLogEntry] = []
    pagination: PaginationInfo

    model_config = ConfigDict(populate_by_name=True)


class AutoCheckoutJobResponse(BaseModel):
    success: bool = True
    message: str
    processedCount: int = Field(0, validation_alias=AliasChoices("processedCount", "processed_count"), serialization_alias="processedCount")
    autoCheckedOutCount: int = Field(0, validation_alias=AliasChoices("autoCheckedOutCount", "auto_checked_out_count"), serialization_alias="autoCheckedOutCount")

    model_config = ConfigDict(populate_by_name=True)

