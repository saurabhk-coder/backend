from fastapi import APIRouter, Body, Depends, HTTPException, BackgroundTasks

import fastapi
from fastapi.exceptions import FastAPIError
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordRequestForm,HTTPBearer
from datetime import timedelta
from sqlalchemy.orm import Session

from ....schemas.auth import AppResetPasswordRequest, CheckUserResponse, GoogleAuthRequest, GoogleAuthResponse, HTMLResponse, UpdateProfile, UpdateProfileResponse, VersionUpdate
from ....services.account_setup import ACCOUNT_SETUP
from ....schemas import  User, Token,SignupRequest,SignupResponse,ResetPasswordRequest,CountryListResponse,BaseResponseSchema
from ....api import deps
from .....core import AppSettings
from ....services import AUTH_SERVICE, SECURITY_SERVICE

auth = APIRouter()


@auth.post("/login", response_model=Token)
def get_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    
    user = AUTH_SERVICE.authenticate(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=AppSettings.API.ACCESS_TOKEN_EXPIRE_MINUTES)
   
    response =SECURITY_SERVICE.create_access_token(user.user_id, access_token_expires)
    return response


@auth.post("/google/login", response_model=Token)
def get_google_token(
    request: GoogleAuthRequest,
    db: Session = Depends(deps.get_db)
) -> Token:
    if request.loginType=='Apple':
        user=AUTH_SERVICE.check_apple_user_exist(db,request.appleId)
    else:
        user=AUTH_SERVICE.check_user_exist(db,request.email)
    if user.user_exist==True:
        if request.loginType=='Apple':
            update_password = AUTH_SERVICE.appleupdatePassword(db,request)
            user = AUTH_SERVICE.appleauthenticate(db, request.appleId, password=request.token)
        else:
            update_password = AUTH_SERVICE.appupdatePassword(db,request)
            user = AUTH_SERVICE.googleauthenticate(db, email=request.email, password=request.token)
    else:
        user_request = SignupRequest
        user_request.firstName = request.firstName
        user_request.middleName = request.middleName
        user_request.password = request.token
        user_request.email = request.email
        user_request.username = request.email
        user_request.appleId = request.appleId
        users = AUTH_SERVICE.appsignup(db, request)


    if request.loginType=='Apple':
        user=AUTH_SERVICE.check_apple_user_exist(db,request.appleId)
    else:   
        user = AUTH_SERVICE.googleauthenticate(db, email=request.email, password=request.token)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=AppSettings.API.ACCESS_TOKEN_EXPIRE_MINUTES)
   
    response =SECURITY_SERVICE.create_access_token(user.user_id, access_token_expires)
    return response

# signup
@auth.post("/signup", response_model=SignupResponse,)
def signup_new_user(
    request: SignupRequest,
    db: Session = Depends(deps.get_db), 
)->SignupResponse:
    user=AUTH_SERVICE.check_user_exist(db,request.email)
    if user.user_exist==True:
        response = SignupResponse
        response.error= True
        response.message="user already exist"
        return response
    else:
        users = AUTH_SERVICE.signup(db, request)
        account_id=users.accountId

        response = SignupResponse
        response.error = False
        response.message="user added"
        
        # project = PROJECT_SERVICE.add_project( users.firstName,users.lastName,users.userId,users.accountId)
        # PROJECT_SETUP.new_project_setup(str(project.projectId),users.firstName,users.lastName,users.accountId,project.projectName)
        return users
    


@auth.put("", response_model=UpdateProfileResponse)
def update_profile(
    *,
    db: Session = Depends(deps.get_db),
    request: UpdateProfile, 
) -> UpdateProfileResponse:
    response=AUTH_SERVICE.update_user(db,request)
    if not response:
        raise HTTPException(status_code=404, detail="Password not update")
    return response




@auth.put("/updatePassword", response_model=BaseResponseSchema)
def update_password(
    *,
    db: Session = Depends(deps.get_db),
    request: ResetPasswordRequest, 
) -> BaseResponseSchema:
    user = AUTH_SERVICE.authenticate(db, email=request.username, password=request.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect  password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    else:
        response=AUTH_SERVICE.reset_password(db,request)
        if not response:
            raise HTTPException(status_code=404, detail="Password not update")
        return response
    
@auth.put("/app/version", response_model=BaseResponseSchema)
def update_version(
    *,
    db: Session = Depends(deps.get_db),
    request: VersionUpdate, 
) -> BaseResponseSchema:
   
    response=AUTH_SERVICE.reset_token(db,request)
    if not response:
        raise HTTPException(status_code=404, detail="app version update")
    return response
    
@auth.put("/reset/Password", response_model=BaseResponseSchema)
def reset_password(
    *,
    db: Session = Depends(deps.get_db),
    request: ResetPasswordRequest, 
) -> BaseResponseSchema:
    
    response=AUTH_SERVICE.reset_password(db,request)
    if not response:
        raise HTTPException(status_code=404, detail="Password not update")
    return response

@auth.put("/app/reset/Password", response_model=BaseResponseSchema)
def app_reset_password(
    *,
    db: Session = Depends(deps.get_db),
    request: AppResetPasswordRequest, 
) -> BaseResponseSchema:
    
    response=AUTH_SERVICE.app_reset_password(db,request)
    if not response:
        raise HTTPException(status_code=404, detail="Password not update")
    return response

@auth.get("/country", response_model=CountryListResponse)
def get_country_list(
    *,
    db: Session = Depends(deps.get_db),
) -> CountryListResponse:
    response=AUTH_SERVICE.get_country_list(db)

    if not response:
        raise HTTPException(status_code=404, detail="Country List not found")
    return response

@auth.get("/checkUser/{username}", response_model=CheckUserResponse)
def check_user_exist(
    *,
    username: str,
    db: Session = Depends(deps.get_db),
) -> CheckUserResponse:
    response=AUTH_SERVICE.check_user_exist(db,username)
    return response

@auth.get('/forgot_password', response_class=HTMLResponse, response_model_exclude_unset=True)
async def ForgetPasswordFromToken( username: str,otp: str, db: Session = Depends(deps.get_db))-> HTMLResponse:
    response=AUTH_SERVICE.ForgetPassword(db,username,otp)
    return HTMLResponse(content=response, status_code=200)

@auth.get('/app/forgot_password', response_class=HTMLResponse, response_model_exclude_unset=True)
async def AppForgetPasswordFromToken( username: str,otp: str, db: Session = Depends(deps.get_db))-> HTMLResponse:
    response=AUTH_SERVICE.AppForgetPassword(db,username,otp)
    return HTMLResponse(content=response, status_code=200)

@auth.get('/password-reset', response_class=HTMLResponse, response_model_exclude_unset=True)
async def PasswordReset( token: str, db: Session = Depends(deps.get_db))-> HTMLResponse:
    response=AUTH_SERVICE.ResetFormManager(db,token)
    return HTMLResponse(content=response, status_code=200) 


def function_names_as_operation_ids(app: fastapi) -> None:
    for route in auth.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name  # in this case, 'read_items'
function_names_as_operation_ids(FastAPIError)
    









