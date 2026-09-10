from .employee_personal_information import employee_personal_information_router
from .employee_department_information import employee_department_information_router
from .employee_account_details import employee_account_details_router
from .employee_professional_information import (
    employee_professional_information_router,
)

__all__ = [
    "employee_personal_information_router",
    "employee_department_information_router",
    "employee_account_details_router",
    "employee_professional_information_router",
]

