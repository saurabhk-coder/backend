from typing import Any, List
from fastapi import APIRouter,  Depends, HTTPException
from sqlalchemy.orm import Session
from .....auth_service.services.auth_service import AUTH_SERVICE
from ....services import USER_SERVICE
from ....schemas import *
from ....api import deps
from fastapi.security import HTTPBearer

users = APIRouter()

@users.get("/me", response_model=Current_user ,dependencies=[Depends(HTTPBearer())])
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: Current_user = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@users.get("/list", response_model=UserListResponse,dependencies=[Depends(HTTPBearer())])
def user_list(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> BaseResponseSchema:
    response=USER_SERVICE.get_user_list(db,current_user.accountId)
    if not response:
        raise HTTPException(status_code=404, detail="UserList Not Found")
    return response

@users.get("/{userId}", response_model=UserDetails,dependencies=[Depends(HTTPBearer())])
def user_details(
    *,
    db: Session = Depends(deps.get_db),
    userId:str,
    # current_user: User = Depends(deps.get_current_active_user),
) -> UserDetails:
    response=USER_SERVICE.get_user_details(db,userId)
    if not response:
        raise HTTPException(status_code=404, detail="UserList Not Found")
    return response

@users.get("/{username}/user", response_model=UserDetails)
def user_details_name(
    *,
    db: Session = Depends(deps.get_db),
    username:str,
    # current_user: User = Depends(deps.get_current_active_user),
) -> UserDetails:
    response=USER_SERVICE.get_user_details_name(db,username)
    if not response:
        raise HTTPException(status_code=404, detail="UserList Not Found")
    return response

# @users.post("/invite", response_model=UserDetails,dependencies=[Depends(HTTPBearer())])
# def InviteUser(
#     *,
#     db: Session = Depends(deps.get_db),
#     request: InviteRequest,
#     current_user: User = Depends(deps.get_current_active_user),
# ) -> UserDetails:
#     response=USER_SERVICE.get_user_details(db,request,current_user.accountId)
#     if not response:
#         raise HTTPException(status_code=404, detail="UserList Not Found")
#     return response

