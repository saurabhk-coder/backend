from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware
from .endpoints import  auth,users
from ....Errors.universal_exception_handler import catch_exceptions_middleware
from ....Errors.validation_exception_handler import ValidationErrorLoggingRoute
from ...core.config import AppSettings
from fastapi import FastAPI


api_router = APIRouter()

# if AppSettings.API.BACKEND_CORS_ORIGINS:
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
    

