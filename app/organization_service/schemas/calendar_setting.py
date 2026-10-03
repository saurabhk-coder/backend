import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

DEFAULT_DAYS_OF_WEEK = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


class WeekendRule(BaseModel):
    first: bool = Field(
        False,
        validation_alias=AliasChoices("1st", "week_1st", "first"),
        serialization_alias="1st",
    )
    second: bool = Field(
        False,
        validation_alias=AliasChoices("2nd", "week_2nd", "second"),
        serialization_alias="2nd",
    )
    third: bool = Field(
        False,
        validation_alias=AliasChoices("3rd", "week_3rd", "third"),
        serialization_alias="3rd",
    )
    fourth: bool = Field(
        False,
        validation_alias=AliasChoices("4th", "week_4th", "fourth"),
        serialization_alias="4th",
    )
    fifth: bool = Field(
        False,
        validation_alias=AliasChoices("5th", "week_5th", "fifth"),
        serialization_alias="5th",
    )
    last: bool = Field(
        False,
        validation_alias=AliasChoices("last", "week_last"),
        serialization_alias="last",
    )
    alt: bool = Field(
        False,
        validation_alias=AliasChoices("alt", "week_alt"),
        serialization_alias="alt",
    )

    model_config = ConfigDict(populate_by_name=True)


class FiscalYearConfig(BaseModel):
    sameAsCalendar: bool = Field(
        True,
        validation_alias=AliasChoices("sameAsCalendar", "same_as_calendar"),
        serialization_alias="sameAsCalendar",
    )
    startMonth: str = Field(
        "January",
        validation_alias=AliasChoices("startMonth", "start_month"),
        serialization_alias="startMonth",
    )
    endMonth: str = Field(
        "December",
        validation_alias=AliasChoices("endMonth", "end_month"),
        serialization_alias="endMonth",
    )

    model_config = ConfigDict(populate_by_name=True)


class LeaveYearConfig(BaseModel):
    sameAsCalendar: bool = Field(
        True,
        validation_alias=AliasChoices("sameAsCalendar", "same_as_calendar"),
        serialization_alias="sameAsCalendar",
    )
    startMonth: str = Field(
        "January",
        validation_alias=AliasChoices("startMonth", "start_month"),
        serialization_alias="startMonth",
    )
    endMonth: str = Field(
        "December",
        validation_alias=AliasChoices("endMonth", "end_month"),
        serialization_alias="endMonth",
    )

    model_config = ConfigDict(populate_by_name=True)


class WorkScheduleConfig(BaseModel):
    maxWorkingHoursPerDay: str = Field(
        "09:00",
        validation_alias=AliasChoices("maxWorkingHoursPerDay", "max_working_hours_per_day"),
        serialization_alias="maxWorkingHoursPerDay",
    )
    weekStartsOn: str = Field(
        "Monday",
        validation_alias=AliasChoices("weekStartsOn", "week_starts_on"),
        serialization_alias="weekStartsOn",
    )
    shiftStartTime: str = Field(
        "09:00",
        validation_alias=AliasChoices("shiftStartTime", "shift_start_time"),
        serialization_alias="shiftStartTime",
    )
    shiftEndTime: str = Field(
        "18:00",
        validation_alias=AliasChoices("shiftEndTime", "shift_end_time"),
        serialization_alias="shiftEndTime",
    )

    model_config = ConfigDict(populate_by_name=True)


class MinimumHoursConfig(BaseModel):
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


def normalize_weekend_definition(
    raw_definition: Optional[Dict[str, Any]],
) -> Dict[str, WeekendRule]:
    """
    Ensure all 7 days of the week are present in the dictionary with complete
    occurrence flags (1st, 2nd, 3rd, 4th, 5th, last, alt).
    """
    raw = raw_definition or {}
    result: Dict[str, WeekendRule] = {}
    for day in DEFAULT_DAYS_OF_WEEK:
        day_val = raw.get(day)
        if isinstance(day_val, WeekendRule):
            result[day] = day_val
        elif isinstance(day_val, dict):
            result[day] = WeekendRule.model_validate(day_val)
        else:
            result[day] = WeekendRule()
    return result


def serialize_weekend_definition_for_db(
    normalized: Dict[str, WeekendRule],
) -> Dict[str, Dict[str, bool]]:
    """
    Convert normalized weekend definition to a raw dictionary with JSON-friendly keys for DB storage.
    """
    return {day: rule.model_dump(by_alias=True) for day, rule in normalized.items()}


class CalendarSettingData(BaseModel):
    id: uuid.UUID
    location: str
    isDefault: bool = Field(
        False,
        validation_alias=AliasChoices("isDefault", "is_default"),
        serialization_alias="isDefault",
    )
    fiscalYear: FiscalYearConfig = Field(
        default_factory=FiscalYearConfig,
        validation_alias=AliasChoices("fiscalYear", "fiscal_year"),
        serialization_alias="fiscalYear",
    )
    leaveYear: LeaveYearConfig = Field(
        default_factory=LeaveYearConfig,
        validation_alias=AliasChoices("leaveYear", "leave_year"),
        serialization_alias="leaveYear",
    )
    workSchedule: WorkScheduleConfig = Field(
        default_factory=WorkScheduleConfig,
        validation_alias=AliasChoices("workSchedule", "work_schedule"),
        serialization_alias="workSchedule",
    )
    minimumHours: MinimumHoursConfig = Field(
        default_factory=MinimumHoursConfig,
        validation_alias=AliasChoices("minimumHours", "minimum_hours"),
        serialization_alias="minimumHours",
    )
    weekendDefinition: Dict[str, WeekendRule] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("weekendDefinition", "weekend_definition"),
        serialization_alias="weekendDefinition",
    )
    organizationId: Optional[uuid.UUID] = Field(
        None,
        validation_alias=AliasChoices("organizationId", "organization_id"),
        serialization_alias="organizationId",
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

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class CalendarSettingCreate(BaseModel):
    location: str = Field(..., min_length=1, max_length=255, description="Branch / office location")
    organizationId: Optional[uuid.UUID] = Field(
        None,
        validation_alias=AliasChoices("organizationId", "organization_id"),
        serialization_alias="organizationId",
    )
    isDefault: Optional[bool] = Field(
        False,
        validation_alias=AliasChoices("isDefault", "is_default"),
        serialization_alias="isDefault",
    )
    fiscalYear: Optional[FiscalYearConfig] = Field(
        default_factory=FiscalYearConfig,
        validation_alias=AliasChoices("fiscalYear", "fiscal_year"),
        serialization_alias="fiscalYear",
    )
    leaveYear: Optional[LeaveYearConfig] = Field(
        default_factory=LeaveYearConfig,
        validation_alias=AliasChoices("leaveYear", "leave_year"),
        serialization_alias="leaveYear",
    )
    workSchedule: Optional[WorkScheduleConfig] = Field(
        default_factory=WorkScheduleConfig,
        validation_alias=AliasChoices("workSchedule", "work_schedule"),
        serialization_alias="workSchedule",
    )
    minimumHours: Optional[MinimumHoursConfig] = Field(
        default_factory=MinimumHoursConfig,
        validation_alias=AliasChoices("minimumHours", "minimum_hours"),
        serialization_alias="minimumHours",
    )
    weekendDefinition: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("weekendDefinition", "weekend_definition"),
        serialization_alias="weekendDefinition",
    )

    model_config = ConfigDict(populate_by_name=True)


class CalendarSettingUpdate(BaseModel):
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    organizationId: Optional[uuid.UUID] = Field(
        None,
        validation_alias=AliasChoices("organizationId", "organization_id"),
        serialization_alias="organizationId",
    )
    isDefault: Optional[bool] = Field(
        None,
        validation_alias=AliasChoices("isDefault", "is_default"),
        serialization_alias="isDefault",
    )
    fiscalYear: Optional[FiscalYearConfig] = Field(
        None,
        validation_alias=AliasChoices("fiscalYear", "fiscal_year"),
        serialization_alias="fiscalYear",
    )
    leaveYear: Optional[LeaveYearConfig] = Field(
        None,
        validation_alias=AliasChoices("leaveYear", "leave_year"),
        serialization_alias="leaveYear",
    )
    workSchedule: Optional[WorkScheduleConfig] = Field(
        None,
        validation_alias=AliasChoices("workSchedule", "work_schedule"),
        serialization_alias="workSchedule",
    )
    minimumHours: Optional[MinimumHoursConfig] = Field(
        None,
        validation_alias=AliasChoices("minimumHours", "minimum_hours"),
        serialization_alias="minimumHours",
    )
    weekendDefinition: Optional[Dict[str, Any]] = Field(
        None,
        validation_alias=AliasChoices("weekendDefinition", "weekend_definition"),
        serialization_alias="weekendDefinition",
    )

    model_config = ConfigDict(populate_by_name=True)


class CalendarSettingListResponse(BaseModel):
    success: bool = True
    data: List[CalendarSettingData] = []

    model_config = ConfigDict(populate_by_name=True)



class CalendarSettingSingleResponse(BaseModel):
    success: bool = True
    data: CalendarSettingData

    model_config = ConfigDict(populate_by_name=True)


class CalendarSettingDeleteResponse(BaseModel):
    success: bool = True
    message: str = "Calendar setting removed successfully (fallback to organization default)"
    id: Optional[uuid.UUID] = None
    location: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)
