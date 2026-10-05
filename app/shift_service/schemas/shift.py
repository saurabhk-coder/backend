import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class MinimumHours(BaseModel):
    fullDay: str = Field(
        "08:00",
        validation_alias=AliasChoices("fullDay", "full_day_hours", "full_day"),
        serialization_alias="fullDay",
    )
    fullDayTolerance: str = Field(
        "00:00",
        validation_alias=AliasChoices("fullDayTolerance", "full_day_tolerance"),
        serialization_alias="fullDayTolerance",
    )
    halfDay: str = Field(
        "04:00",
        validation_alias=AliasChoices("halfDay", "half_day_hours", "half_day"),
        serialization_alias="halfDay",
    )
    halfDayTolerance: str = Field(
        "00:00",
        validation_alias=AliasChoices("halfDayTolerance", "half_day_tolerance"),
        serialization_alias="halfDayTolerance",
    )

    model_config = ConfigDict(populate_by_name=True)


class GracePeriodPolicy(BaseModel):
    enabled: bool = Field(
        False,
        validation_alias=AliasChoices("enabled", "is_enabled"),
        serialization_alias="enabled",
    )
    lateCheckInMinutes: int = Field(
        0,
        validation_alias=AliasChoices("lateCheckInMinutes", "late_check_in_minutes"),
        serialization_alias="lateCheckInMinutes",
    )
    earlyCheckOutMinutes: int = Field(
        0,
        validation_alias=AliasChoices("earlyCheckOutMinutes", "early_check_out_minutes"),
        serialization_alias="earlyCheckOutMinutes",
    )

    model_config = ConfigDict(populate_by_name=True)


class ReminderDetail(BaseModel):
    enabled: bool = Field(
        False,
        validation_alias=AliasChoices("enabled", "is_enabled"),
        serialization_alias="enabled",
    )
    beforeTime: str = Field(
        "00:00",
        validation_alias=AliasChoices("beforeTime", "before_time"),
        serialization_alias="beforeTime",
    )
    afterTime: str = Field(
        "00:00",
        validation_alias=AliasChoices("afterTime", "after_time"),
        serialization_alias="afterTime",
    )

    model_config = ConfigDict(populate_by_name=True)


class ShiftReminder(BaseModel):
    checkIn: ReminderDetail = Field(
        default_factory=ReminderDetail,
        validation_alias=AliasChoices("checkIn", "check_in"),
        serialization_alias="checkIn",
    )
    checkOut: ReminderDetail = Field(
        default_factory=ReminderDetail,
        validation_alias=AliasChoices("checkOut", "check_out"),
        serialization_alias="checkOut",
    )

    model_config = ConfigDict(populate_by_name=True)


class ShiftResponse(BaseModel):
    id: uuid.UUID
    name: str
    startTime: str = Field(
        ...,
        validation_alias=AliasChoices("startTime", "start_time"),
        serialization_alias="startTime",
    )
    endTime: str = Field(
        ...,
        validation_alias=AliasChoices("endTime", "end_time"),
        serialization_alias="endTime",
    )
    shiftDuration: str = Field(
        "09:00",
        validation_alias=AliasChoices("shiftDuration", "shift_duration"),
        serialization_alias="shiftDuration",
    )
    startDate: Optional[date] = Field(
        None,
        validation_alias=AliasChoices("startDate", "start_date"),
        serialization_alias="startDate",
    )
    endDate: Optional[date] = Field(
        None,
        validation_alias=AliasChoices("endDate", "end_date"),
        serialization_alias="endDate",
    )
    peopleRequired: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("peopleRequired", "people_required"),
        serialization_alias="peopleRequired",
    )
    color: str = Field(
        "#F05A28",
        validation_alias=AliasChoices("color"),
        serialization_alias="color",
    )
    workArea: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("workArea", "work_area"),
        serialization_alias="workArea",
    )
    department: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("department"),
        serialization_alias="department",
    )
    location: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("location"),
        serialization_alias="location",
    )
    payCalculationType: str = Field(
        "per_day",
        validation_alias=AliasChoices("payCalculationType", "pay_calculation_type"),
        serialization_alias="payCalculationType",
    )
    minimumHours: MinimumHours = Field(
        default_factory=MinimumHours,
        validation_alias=AliasChoices("minimumHours", "minimum_hours"),
        serialization_alias="minimumHours",
    )
    recurrencePattern: str = Field(
        "daily",
        validation_alias=AliasChoices("recurrencePattern", "recurrence_pattern"),
        serialization_alias="recurrencePattern",
    )
    weeklyDays: List[str] = Field(
        default_factory=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri"],
        validation_alias=AliasChoices("weeklyDays", "weekly_days", "weekly_working_days"),
        serialization_alias="weeklyDays",
    )
    calendarWeekendPolicy: str = Field(
        "calendar",
        validation_alias=AliasChoices("calendarWeekendPolicy", "calendar_weekend_policy"),
        serialization_alias="calendarWeekendPolicy",
    )
    gracePeriodPolicy: GracePeriodPolicy = Field(
        default_factory=GracePeriodPolicy,
        validation_alias=AliasChoices("gracePeriodPolicy", "grace_period_policy"),
        serialization_alias="gracePeriodPolicy",
    )
    shiftReminder: ShiftReminder = Field(
        default_factory=ShiftReminder,
        validation_alias=AliasChoices("shiftReminder", "shift_reminder"),
        serialization_alias="shiftReminder",
    )
    isActive: bool = Field(
        True,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )
    createdAt: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )
    updatedAt: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("updatedAt", "updated_at"),
        serialization_alias="updatedAt",
    )
    organizationId: Optional[uuid.UUID] = Field(
        None,
        validation_alias=AliasChoices("organizationId", "organization_id"),
        serialization_alias="organizationId",
    )

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ShiftCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Shift display name")
    startTime: str = Field(
        ...,
        validation_alias=AliasChoices("startTime", "start_time"),
        serialization_alias="startTime",
        description="Shift start time (e.g. '09:00')",
    )
    endTime: str = Field(
        ...,
        validation_alias=AliasChoices("endTime", "end_time"),
        serialization_alias="endTime",
        description="Shift end time (e.g. '18:00')",
    )
    shiftDuration: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("shiftDuration", "shift_duration"),
        serialization_alias="shiftDuration",
    )
    startDate: Optional[date] = Field(
        None,
        validation_alias=AliasChoices("startDate", "start_date"),
        serialization_alias="startDate",
    )
    endDate: Optional[date] = Field(
        None,
        validation_alias=AliasChoices("endDate", "end_date"),
        serialization_alias="endDate",
    )
    peopleRequired: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("peopleRequired", "people_required"),
        serialization_alias="peopleRequired",
    )
    color: Optional[str] = Field(
        "#F05A28",
        validation_alias=AliasChoices("color"),
        serialization_alias="color",
    )
    workArea: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("workArea", "work_area"),
        serialization_alias="workArea",
    )
    department: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("department"),
        serialization_alias="department",
    )
    location: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("location"),
        serialization_alias="location",
    )
    payCalculationType: Optional[str] = Field(
        "per_day",
        validation_alias=AliasChoices("payCalculationType", "pay_calculation_type"),
        serialization_alias="payCalculationType",
    )
    minimumHours: Optional[MinimumHours] = Field(
        default_factory=MinimumHours,
        validation_alias=AliasChoices("minimumHours", "minimum_hours"),
        serialization_alias="minimumHours",
    )
    recurrencePattern: Optional[str] = Field(
        "daily",
        validation_alias=AliasChoices("recurrencePattern", "recurrence_pattern"),
        serialization_alias="recurrencePattern",
    )
    weeklyDays: Optional[List[str]] = Field(
        default_factory=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri"],
        validation_alias=AliasChoices("weeklyDays", "weekly_days", "weekly_working_days"),
        serialization_alias="weeklyDays",
    )
    calendarWeekendPolicy: Optional[str] = Field(
        "calendar",
        validation_alias=AliasChoices("calendarWeekendPolicy", "calendar_weekend_policy"),
        serialization_alias="calendarWeekendPolicy",
    )
    gracePeriodPolicy: Optional[GracePeriodPolicy] = Field(
        default_factory=GracePeriodPolicy,
        validation_alias=AliasChoices("gracePeriodPolicy", "grace_period_policy"),
        serialization_alias="gracePeriodPolicy",
    )
    shiftReminder: Optional[ShiftReminder] = Field(
        default_factory=ShiftReminder,
        validation_alias=AliasChoices("shiftReminder", "shift_reminder"),
        serialization_alias="shiftReminder",
    )
    isActive: Optional[bool] = Field(
        True,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )
    organizationId: Optional[uuid.UUID] = Field(
        None,
        validation_alias=AliasChoices("organizationId", "organization_id"),
        serialization_alias="organizationId",
    )

    model_config = ConfigDict(populate_by_name=True)


class ShiftUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    startTime: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("startTime", "start_time"),
        serialization_alias="startTime",
    )
    endTime: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("endTime", "end_time"),
        serialization_alias="endTime",
    )
    shiftDuration: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("shiftDuration", "shift_duration"),
        serialization_alias="shiftDuration",
    )
    startDate: Optional[date] = Field(
        None,
        validation_alias=AliasChoices("startDate", "start_date"),
        serialization_alias="startDate",
    )
    endDate: Optional[date] = Field(
        None,
        validation_alias=AliasChoices("endDate", "end_date"),
        serialization_alias="endDate",
    )
    peopleRequired: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("peopleRequired", "people_required"),
        serialization_alias="peopleRequired",
    )
    color: Optional[str] = Field(None, validation_alias=AliasChoices("color"), serialization_alias="color")
    workArea: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("workArea", "work_area"),
        serialization_alias="workArea",
    )
    department: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("department"),
        serialization_alias="department",
    )
    location: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("location"),
        serialization_alias="location",
    )
    payCalculationType: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("payCalculationType", "pay_calculation_type"),
        serialization_alias="payCalculationType",
    )
    minimumHours: Optional[MinimumHours] = Field(
        None,
        validation_alias=AliasChoices("minimumHours", "minimum_hours"),
        serialization_alias="minimumHours",
    )
    recurrencePattern: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("recurrencePattern", "recurrence_pattern"),
        serialization_alias="recurrencePattern",
    )
    weeklyDays: Optional[List[str]] = Field(
        None,
        validation_alias=AliasChoices("weeklyDays", "weekly_days", "weekly_working_days"),
        serialization_alias="weeklyDays",
    )
    calendarWeekendPolicy: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("calendarWeekendPolicy", "calendar_weekend_policy"),
        serialization_alias="calendarWeekendPolicy",
    )
    gracePeriodPolicy: Optional[GracePeriodPolicy] = Field(
        None,
        validation_alias=AliasChoices("gracePeriodPolicy", "grace_period_policy"),
        serialization_alias="gracePeriodPolicy",
    )
    shiftReminder: Optional[ShiftReminder] = Field(
        None,
        validation_alias=AliasChoices("shiftReminder", "shift_reminder"),
        serialization_alias="shiftReminder",
    )
    isActive: Optional[bool] = Field(
        None,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )
    organizationId: Optional[uuid.UUID] = Field(
        None,
        validation_alias=AliasChoices("organizationId", "organization_id"),
        serialization_alias="organizationId",
    )

    model_config = ConfigDict(populate_by_name=True)


class PaginationInfo(BaseModel):
    page: int = 1
    pageSize: int = Field(20, serialization_alias="pageSize")
    total: int = 0
    totalPages: int = Field(1, serialization_alias="totalPages")

    model_config = ConfigDict(populate_by_name=True)


class ShiftListResponse(BaseModel):
    success: bool = True
    data: List[ShiftResponse] = []
    pagination: PaginationInfo

    model_config = ConfigDict(populate_by_name=True)


class ShiftDeleteResponse(BaseModel):
    success: bool = True
    message: str = "Shift deleted successfully"

    model_config = ConfigDict(populate_by_name=True)
