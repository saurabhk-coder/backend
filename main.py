from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
# from app.core.middleware.opensensus_middleware import add_opensense
from app.core.middleware.validation_exception_handler import ValidationErrorLoggingRoute
from app.auth_service.api.api_v1.endpoints import  auth as auth_routes
from app.user_service.api.api_v1.endpoints import  users as api_users
from app.role_service.api.api_v1.endpoints import roles as api_roles
from app.organization_service.api.api_v1.endpoints import organizations as api_organizations
from app.organization_service.api.api_v1.endpoints import organization_settings as api_org_settings
from app.employee_service.api.api_v1.endpoints import (
    employee_personal_information_router as api_employee_personal_info,
    employee_department_information_router as api_employee_dept_info,
    employee_account_details_router as api_employee_account_details,
)
from app.core import AppSettings
from app.auth_service.services.securityservice import SECURITY_SERVICE

# from app.core.middleware.opensensus_middleware2 import middlewareOpencensus


def get_application() -> FastAPI:
    #application = FastAPI()
    application = FastAPI(
    title="aaralia API",
    # root_path = "/api/auth",
    openapi_url=f"{AppSettings.API.API_V1_STR}/openapi.json",
    version="1.0.1",
        )
    
    add_middlewares(application)
    add_auth_routes(application)
    add_user_routes(application)
    add_role_routes(application)
    add_organization_routes(application)
    add_organization_settings_routes(application)
    add_employee_personal_information_routes(application)
    add_employee_department_information_routes(application)
    add_employee_account_details_routes(application)
   

    application.router.route_class = ValidationErrorLoggingRoute
    return application

def add_middlewares(application:FastAPI):
    application.add_middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                     )
    # application.middleware('http')(add_opensense)
    # application.middleware('http')(middlewareOpencensus)

    # application.middleware('http')(catch_exceptions_middleware)
    return application

def add_auth_routes(application:FastAPI):
    application.include_router(auth_routes.auth, prefix='/api/v1/auth', tags=['Auth'])
    SECURITY_SERVICE.update_schema_name(application, auth_routes.get_access_token, "AccessToken")
    return application

def add_user_routes(application:FastAPI):
    application.include_router(api_users.users, prefix='/api/v1/user', tags=['User'])
    return application 

def add_role_routes(application:FastAPI):
    application.include_router(api_roles.roles, prefix='/api/v1/roles', tags=['Roles'])
    application.include_router(api_roles.roles, prefix='/roles', tags=['Roles'])
    return application 

def add_organization_routes(application:FastAPI):
    application.include_router(api_organizations.organizations, prefix='/api/v1/organizations', tags=['Organizations'])
    application.include_router(api_organizations.organizations, prefix='/organizations', tags=['Organizations'])
    return application 

def add_organization_settings_routes(application:FastAPI):
    application.include_router(api_org_settings.organization_settings, prefix='/api/v1', tags=['Organization Settings'])
    application.include_router(api_org_settings.organization_settings, tags=['Organization Settings'])
    return application 

def add_employee_personal_information_routes(application:FastAPI):
    application.include_router(api_employee_personal_info, prefix='/api/v1', tags=['Employee Personal Information'])
    return application 

def add_employee_department_information_routes(application:FastAPI):
    application.include_router(api_employee_dept_info, prefix='/api/v1', tags=['Employee Department Information'])
    return application 

def add_employee_account_details_routes(application:FastAPI):
    application.include_router(api_employee_account_details, prefix='/api/v1', tags=['Employee Account Details'])
    return application 


app = get_application()




