from datetime import timedelta
import json
from sqlalchemy.orm import Session

from app.user_service.crud.crud_user import CRUD_USER

from ...core.config import AppSettings
from app.auth_service.schemas.auth import HTMLResponse, UpdateProfile, UpdateProfileResponse

from app.core.default_config.account_setup import ACCOUNT_CONFIGURATION
from app.core.default_config.email_config import EmailConfig
from app.core.default_config.html_config import HtmlMsgConfig
from app.user_service.schemas.user import UserListResponse, Users
from ..schemas import *
from .securityservice import SECURITY_SERVICE, SecurityService
from abc import *
from ..crud import *


class IAuthService(ABC):
    @abstractmethod
    def authenticate(db:Session,email:str,password:str) ->User:
       pass
    @abstractmethod
    def appleauthenticate(db:Session,appleId:str,password:str) ->User:
       pass

    @abstractmethod
    def signup(db:Session,request:SignupRequest) ->User:
       pass

    @abstractmethod
    def appsignup(db:Session,request:SignupRequest) ->User:
       pass

    @abstractmethod
    def reset_password(db:Session,request:ResetPasswordRequest) ->User:
       pass

    @abstractmethod
    def reset_token(db:Session,request:VersionUpdate) ->BaseResponseSchema:
       pass

    @abstractmethod
    def app_reset_password(db:Session,request:AppResetPasswordRequest) ->User:
       pass

    @abstractmethod
    def get_country_list(db:Session) ->CountryListResponse:
       pass
    @abstractmethod
    def get_user(self,db:Session,id:str) ->User:
        pass
    @abstractmethod
    def check_user_exist(self,db:Session,email:str) ->User:
        pass

    @abstractmethod
    def check_apple_user_exist(self,db:Session,email:str) ->User:
        pass

    @abstractmethod
    def ForgetPassword(self,db:Session,email:str,otp) ->User:
        pass

    @abstractmethod
    def AppForgetPassword(self,db:Session,email:str,otp:str) ->User:
        pass

    @abstractmethod
    def ResetFormManager(self,db:Session,token:str) ->HTMLResponse:
        pass

    @abstractmethod
    def update_user(self,db:Session,request:UpdateProfile) ->User:
        pass

    @abstractmethod
    def appupdatePassword(self,db:Session,request:GoogleAuthRequest) ->User:
        pass

    @abstractmethod
    def appleupdatePassword(self,db:Session,request:GoogleAuthRequest) ->User:
        pass

    @abstractmethod
    def googleauthenticate(self,db:Session,email:str,password:str) ->User:
        pass




class AuthService(IAuthService):

    def authenticate(self,db:Session,email:str,password:str) ->User:
        user = CRUD_USER.get_by_email(db, email=email)
        if not user:
            return None
        if not SECURITY_SERVICE.verify_password(password, user.password_salt):
            return None
        return user
    
    def googleauthenticate(self,db:Session,email:str,password:str) ->User:
        user = CRUD_USER.get_by_email(db, email=email)
        # if not user:
        #     return None
        # if not SECURITY_SERVICE.verify_password(password, user.token):
        #     return None
        return user
    
    def appleauthenticate(self,db:Session,appleId:str,password:str) ->User:
        user = CRUD_USER.get_by_apple(db, appleId)
        if not user:
            return None
        if not SECURITY_SERVICE.verify_password(password, user.token):
            return None
        return user

    def signup(self,db:Session,request:SignupRequest)->SignupResponse:
        db_request = SignupDBRequest
        db_request.firstName = request.firstName
        db_request.email = request.email
        db_request.username = request.username
        db_request.lastName = request.lastName,
        db_request.password_salt = request.password,
        db_request.isActive = True
        db_request.countryCode = request.countryCode
        response = SignupResponse
        response.username = user.username
        response.firstName = user.first_name
        response.lastName = request.lastName
        response.email = user.email
        response.countryCode = user.country_code
        response.isActive = user.is_active
        response.profileImage = user.profile_image
        response.mobileNumber = user.mobile_number
        response.userId = str(user.user_id)
        return response
    
    def appsignup(self,db:Session,request:SignupRequest)->SignupResponse:
        db_request = SignupDBRequest
        db_request.firstName = request.firstName
        db_request.email = request.email
        db_request.username = request.email
        db_request.lastName = request.lastName,
        db_request.password_salt = request.token,
        db_request.isActive = True
        db_request.countryCode = "IN"
        db_request.appleId = request.appleId
        account = CRUD_USER.add_new_account(db,str(''))
        db_request.accountId = account.id		
        container_name = 'c-'
        user = CRUD_USER.add_app_user(db, db_request,container_name)
        response = SignupResponse
        response.username = user.username
        response.firstName = user.first_name
        response.lastName = request.lastName
        response.email = user.email
        response.countryCode = user.country_code
        response.isActive = user.is_active
        response.accountId = str(account.id)
        response.containerName = container_name
        response.profileImage = user.profile_image
        response.mobileNumber = user.mobile_number
        response.userId = str(user.user_id)
        return response

    def add_user(self,db:Session,request:SignupRequest,accountId)->SignupResponse:
        db_request = SignupDBRequest
        db_request.firstName = request.firstName
        db_request.email = request.email
        db_request.password_salt = request.password
        db_request.username = request.username
        db_request.lastName = request.lastName,
        db_request.isActive = False
        db_request.countryCode = request.countryCode
        db_request.accountId = accountId
        db_request.profileImage = request.profileImage
        db_request.mobileNumber = request.mobileNumber
        user = CRUD_USER.add_user(db, db_request)
        token_model = SecurityService().create_access_token(user)
        response = SignupResponse
        response.username = user.username
        response.firstName = user.firstName
        response.lastName = str(user.lastName)
        response.email = user.email
        response.countryCode = user.countryCode
        response.isActive = user.isActive
        response.accountId = str(accountId)
        response.containerName = ""
        return response
       
    
    def get_user(self,db:Session,id:str) ->User:
        user = CRUD_USER.get_user_byid(db, id=id)
        return user

    def reset_password(self,db:Session,request:ResetPasswordRequest)->BaseResponseSchema:
        passwordSalt= request.confirmPassword
        user = CRUD_USER.update_password(db, passwordSalt,request.username)
        response = BaseResponseSchema
        response.message = "Password has been Updated"
        
        return user
    
    def reset_token(self,db:Session,request:VersionUpdate) ->BaseResponseSchema:
        user = CRUD_USER.update_version(db, request)
        response = BaseResponseSchema
        response.message = "Password has been Updated"
        
        return user
    
    def appupdatePassword(self,db:Session,request:GoogleAuthRequest) ->User:
        passwordSalt= request.token
        user = CRUD_USER.update_app_password(db, passwordSalt,request.email)
        response = BaseResponseSchema
        response.message = "Password has been Updated"
        
        return user
    
    def appleupdatePassword(self,db:Session,request:GoogleAuthRequest) ->User:
        passwordSalt= request.token
        user = CRUD_USER.update_apple_password(db, passwordSalt,request.appleId)
        response = BaseResponseSchema
        response.message = "Password has been Updated"
        
        return user
    
    def app_reset_password(self,db:Session,request:AppResetPasswordRequest)->BaseResponseSchema:
        passwordSalt= request.password
        check_otp = CRUD_USER.check_otp(db,request.username,request.otp)
        if check_otp==True:
            user = CRUD_USER.update_app_password(db, passwordSalt,request.username)
            response = BaseResponseSchema
            response.message = "Password has been Updated"
        else:
            response = BaseResponseSchema
            response.message = "Otp doesn't matched"
        
        return response
    
    def ResetFormManager(self, db: Session, token: str)->HTMLResponse:
        user_dict = SecurityService().decodeJWT(token)
        userid = user_dict['sub']
        user = CRUD_USER.get_by_email(db, userid)
        if user is None:
            html_content = HtmlMsgConfig.NONE_MSG
        else:
            html_content = HtmlMsgConfig.INPUT_PASSWORD.format(form_url=EmailConfig.SAVE_URL, username=user.username)
            
        return html_content	
    
    def update_user(self,db:Session,request:UpdateProfile) ->User:
        user = CRUD_USER.update_user(db, request)
        response = UpdateProfileResponse
        response.message = "User Updated"
        response.firstName = user.first_name
        response.lastName = user.last_name
        response.countryCode = user.country_code
        response.profileImage = user.profile_image
        response.mobileNumber = user.mobile_number
        response.doj = str(user.doj)
        response.dob = user.dob
        response.state = user.state
        response.organisation = user.organisation
        response.designation = user.designation
        response.about = user.about
        
        return response

    def get_country_list(self,db:Session) ->CountryListResponse:
        country_list = CRUD_USER.get_country_list(db)
        response:CountryListResponse = CountryListResponse(country=[])
        for lst in country_list:
            countrylst:Country=Country(
                countryCode=lst.country_code,
                countryName=lst.country_name

            )
            response.country.append(countrylst)
        return response

    def get_user_list(self,db:Session,accountId:str) ->UserListResponse:
        user_list = CRUD_USER.get_user_list(db,accountId)
        response:UserListResponse =UserListResponse(users=[])
        for lst in user_list:
            user_data:Users=Users(
            user_id= str(lst.user_id),
            firstName = lst.firstName,
            lastName = lst.lastName,
            email= lst.email,
            username= lst.username,
            accountId = str(lst.accountId),
            profile_image = lst.profile_image,
            mobile_number = lst.mobile_number
            
            )
            response.users.append(user_data)
        return response

    def get_user_list_name(self,db:Session,firstName:str,accountId:str) ->UserListResponse:
        user_list = CRUD_USER.get_user_list_name(db,firstName,accountId)
        response:UserListResponse =UserListResponse(users=[])
        for lst in user_list:
            user_data:Users=Users(
            user_id= str(lst.user_id),
            firstName = lst.firstName,
            lastName = lst.lastName,
            email= lst.email,
            username= lst.username,
            accountId = str(lst.accountId)
            
            )
            response.users.append(user_data)
        return response

    def AppForgetPassword(self,db:Session,username:str,otp) ->UserListResponse:
        user = CRUD_USER.get_by_email(db,username)
        access_token_expires = timedelta(minutes=AppSettings.API.ACCESS_TOKEN_EXPIRE_MINUTES)
        token_model =SECURITY_SERVICE.create_access_token(username, access_token_expires)
        if user is not None:
            html_content = HtmlMsgConfig.SUCCESS_MSG
        else:
            html_content = HtmlMsgConfig.NONE_MSG
         
        return html_content
    
    def ForgetPassword(self,db:Session,username:str,otp:str) ->UserListResponse:
        user = CRUD_USER.get_by_email(db,username)
        access_token_expires = timedelta(minutes=AppSettings.API.ACCESS_TOKEN_EXPIRE_MINUTES)
        token_model =SECURITY_SERVICE.create_access_token(username, access_token_expires)
        if user is not None:
            user = CRUD_USER.user_otp(db,username,otp)
            html_content = HtmlMsgConfig.SUCCESS_MSG
        else:
            html_content = HtmlMsgConfig.NONE_MSG
         
        return html_content
        

    
	

    def check_user_exist(self,db:Session,username:str) ->CheckUserResponse:
        user = CRUD_USER.verify_user_exist(db,username)
        response = CheckUserResponse
        response.user_exist = user
        if user==True:
            response.message ="User Exist"
        else:
            response.message = "User Not Exist"
        return response
    
    def check_apple_user_exist(self,db:Session,appleId:str) ->CheckUserResponse:
        user = CRUD_USER.verify_apple_user_exist(db,appleId)
        response = CheckUserResponse
        response.user_exist = user
        if user==True:
            response.message ="User Exist"
        else:
            response.message = "User Not Exist"
        return response

AUTH_SERVICE:IAuthService = AuthService()