from typing import Any, List
from fastapi import APIRouter,  Depends
import fastapi
from fastapi.exceptions import FastAPIError
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from ....schemas import User
from ....api import deps
from fastapi.security import HTTPBearer


router = APIRouter()



@router.get("/meh", response_model=User,dependencies=[Depends(HTTPBearer())])
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> User:
    """
    Get current user.
    """
    return current_user

@router.get("/mee",response_model=User,dependencies=[Depends(HTTPBearer())])
def get_file(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    file_id:str
    
) -> User:
    # response =  FILE_SERVICE.get_file(db,file_id, current_user)
    # if not response:
    #     raise HTTPException(status_code=404, detail="File not found")
    return "response"

def function_names_as_operation_ids(app: fastapi) -> None:
    for route in router.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name  # in this case, 'read_items'
function_names_as_operation_ids(FastAPIError)

