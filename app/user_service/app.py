from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.auth_service.api.api_v1.endpoints import  auth as api_router
from app.Errors.universal_exception_handler import catch_exceptions_middleware
from app.Errors.validation_exception_handler import ValidationErrorLoggingRoute
from starlette.middleware.sessions import SessionMiddleware

def get_application() -> FastAPI:
    application = FastAPI(
                title="Twinn API",
                version="1.0.0",
        )
    add_middlewares(application)
    application.add_middleware(SessionMiddleware, secret_key="!secret")
    add_auth_routes(application)

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
    
    application.middleware('http')(catch_exceptions_middleware)
    return application



def add_auth_routes(application:FastAPI):
    application.include_router(api_router.auth, prefix='/api/v1/auth', tags=['Auth'])
    return application 
  



