from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from starlette.responses import JSONResponse



async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500, )
