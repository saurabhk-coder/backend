from fastapi import  FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.middleware.universal_exception_handler import catch_exceptions_middleware
from app.middleware.validation_exception_handler import ValidationErrorLoggingRoute

def get_application() -> FastAPI:
    application = FastAPI(
                title="Twinn Auth API",
                description="API's for future.",
                version="1.0.0",
        )
    add_middlewares(application)
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



  



