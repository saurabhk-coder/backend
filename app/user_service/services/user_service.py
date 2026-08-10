from sqlalchemy.orm import Session

from app.user_service.schemas.user import *

from ..models import user
from ..schemas import *
from .securityservice import SECURITY_SERVICE
from ..crud.crud_user import CRUD_USER
from abc import *

class IUserService(ABC):
    @abstractmethod
    def authenticate(db:Session,email:str,password:str) ->User:
       pass

  
    @abstractmethod
    def reset_password(db:Session,request:ResetPasswordRequest) ->User:
       pass
    @abstractmethod
    def get_country_list(db:Session) ->CountryListResponse:
       pass
    @abstractmethod
    def get_user(self,db:Session,id:str) ->User:
        pass

    @abstractmethod
    def get_user_me(self,db:Session,id:str) ->User:
        pass
    @abstractmethod
    def check_user_exist(self,db:Session,email:str) ->User:
        pass
    @abstractmethod
    def get_user_list(self,db:Session,id:str) ->User:
        pass
    @abstractmethod
    def get_user_details(self,db:Session,userId:str) ->User:
        pass

    @abstractmethod
    def get_user_details_name(self,db:Session,username:str) ->User:
        pass




class UserService(IUserService):

    def authenticate(self,db:Session,email:str,password:str) ->User:
        user = CRUD_USER.get_by_email(db, email=email)
        if not user:
            return None
        if not SECURITY_SERVICE.verify_password(password, user.password_salt):
            return None
        return user

   
    
    def get_user(self,db:Session,id:str) ->User:
        user = CRUD_USER.get_user_byid(db, id=id)
        return user
    
    def get_user_me(self,db:Session,id:str) ->User:
        user = CRUD_USER.get_user_me(db, id=id)
        return user

    def get_user_list(self,db:Session,account_id:str) ->UserListResponse:
        user_list = CRUD_USER.get_user_list(db,account_id)
        response:UserListResponse =UserListResponse(users=[])
        for lst in user_list:
            user_data:Users=Users(
            userId= str(lst.user_id),
            firstName = lst.first_name,
            lastName = lst.last_name,
            email= lst.email,
            username= lst.username,
            accountId = str(lst.account_id),
            profileImage = lst.profile_image,
            mobileNumber = lst.mobile_number,
            isactive = lst.is_active
            )
            response.users.append(user_data)
        return response

    def get_user_details(self,db:Session,userId:str,) ->UserDetails:
        user = CRUD_USER.get_user_details(db,userId)
        response= UserDetails
        response.userId = str(user.user_id)
        response.firstName = user.first_name
        response.lastName = user.last_name
        response.email = user.email
        response.about = user.about
        response.profileImage = user.profile_image
        response.username = user.username
        response.countryCode = user.country_code
        response.doj = user.doj
        response.dob = user.dob
        response.organisation = user.organisation
        response.designation = user.designation
        response.about = user.about
        response.state = user.state
        response.creditPoints = user.credit_points
    
        return response
    
    def get_user_details_name(self,db:Session,username:str,) ->UserDetails:
        user = CRUD_USER.get_user_details_name(db,username)
        response= UserDetails
        response.userId = str(user.user_id)
        response.firstName = user.first_name
        response.lastName = user.last_name
        response.email = user.email
        response.about = user.about
        response.profileImage = user.profile_image
        response.username = user.username
        response.countryCode = user.country_code
        response.doj = user.doj
        response.dob = user.dob
        response.organisation = user.organisation
        response.designation = user.designation
        response.about = user.about
        response.state = user.state
        response.creditPoints = user.credit_points
    
        return response

    def reset_password(self,db:Session,request:ResetPasswordRequest,user_id:str)->BaseResponseSchema:
        password_salt= request.password
        user = CRUD_USER.update_password(db, password_salt,user_id)
        response = BaseResponseSchema
        response.message = "User"
        
        return user

    def get_country_list(self,db:Session) ->CountryListResponse:
        country_list = CRUD_USER.get_country_list(db)
        return country_list

    def check_user_exist(self,db:Session,username:str) ->CheckUserResponse:
        user = CRUD_USER.verify_user_exist(db,username)
        response = CheckUserResponse
        response.user_exist = user
        if user==True:
            response.message ="User Exist"
        else:
            response.message = "User Not Exist"
        return response

USER_SERVICE:IUserService = UserService()