from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
# from app.core.middleware.opensensus_middleware import add_opensense
from app.core.middleware.validation_exception_handler import ValidationErrorLoggingRoute
from app.auth_service.api.api_v1.endpoints import  auth as auth_routes
from app.user_service.api.api_v1.endpoints import  users as api_users
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




app = get_application()




