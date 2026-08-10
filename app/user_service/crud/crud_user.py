from datetime import date, timedelta
from typing import Any, Dict, Optional, Union,List
from sqlalchemy.orm import Session
from app.auth_service.models import UserDb,CountryDB
from app.auth_service.models.user import AccountDb, FolderDB
from ..schemas import User,CountryDbResponse
from passlib.context import CryptContext



class CRUDUser():
	def __init__(self):
		self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

	def __get_password_hash(self, password: str):
		return self.pwd_context.hash(password[0])
	
	def __get_new_password_hash(self, password: str):
		return self.pwd_context.hash(password)
   
	def get_by_email(self, db: Session,  email: str) -> Optional[UserDb]:
		return db.query(UserDb).filter((UserDb.email).ilike(email)).first()
	
	def get_by_apple(self, db: Session,  appleId: str) -> Optional[UserDb]:
		return db.query(UserDb).filter((UserDb.apple_id).ilike(appleId)).first()
	
	def get_user_byid(self, db: Session, *, id: int) -> Optional[UserDb]:
		return db.query(UserDb).filter((UserDb.user_id == id)).first()
	
	def get_user_me(self, db: Session, *, id: int) -> Optional[UserDb]:
		return db.query(UserDb).filter((UserDb.username == id)).first()

	

	def get_user_list(self, db: Session,account_id: str) -> List[UserDb]:
		return db.query(UserDb).filter(UserDb.account_id == account_id).all()

	def get_user_details(self, db: Session,user_id:str) -> List[UserDb]:
		return db.query(UserDb).filter( (UserDb.user_id==user_id)).first()
	
	def get_user_details_name(self, db: Session,user_id:str) -> List[UserDb]:
		return db.query(UserDb).filter( (UserDb.username==user_id)).first()

	# def add_new_user(self, db: Session, user:UserDb)-> User:
	# 	hashed_password = self.__get_password_hash(user.password_salt)
	# 	db_signup: UserDb = UserDb( first_name = user.first_name, 
	# 								last_name = user.last_name,
	# 								password_salt = hashed_password,
	# 								username = user.username,
	# 								email = user.email,
	# 								country_code = user.country_code
	# 							)

	# 	db.add(db_signup)
	# 	db.commit()
	# 	db.refresh(db_signup)	
	# 	return db_signup
	
	def add_new_account(self, db: Session, account_name:str)-> AccountDb:
		db_account: AccountDb = AccountDb( account_name = account_name, 
									
								)

		db.add(db_account)
		db.commit()
		db.refresh(db_account)
		# if db_account.account_name=="":
		# 	user_db=db.query(AccountDb).filter(AccountDb.id == db_account.id).first()
		# 	user_db.account_name = 'Account'+str(db_account.id)
		# 	db.commit()

		return db_account
	
	def user_otp(self, db: Session, username:str,otp:str)-> UserDb:
		user_db=db.query(UserDb).filter(UserDb.username == username).first()
		user_db.otp = otp
		db.commit()
		db.refresh(user_db)
		# if db_account.account_name=="":
		# 	user_db=db.query(AccountDb).filter(AccountDb.id == db_account.id).first()
		# 	user_db.account_name = 'Account'+str(db_account.id)
		# 	db.commit()

		return user_db
	
	def add_new_user(self, db: Session, user:UserDb,container_name)-> UserDb:

		hashed_password = self.__get_password_hash(user.password_salt)
		db_signup: UserDb = UserDb( first_name = user.firstName, 
									last_name = user.lastName,
									password_salt = hashed_password,
									username = user.email,
									email = user.email,
									credit_points = 50,
									# country_code = user.countryCode,
									account_id = user.accountId,
									container_name = container_name
								)

		db.add(db_signup)
		db.commit()
		
		db.commit()
		db.close()
		# db.refresh(db_signup)	
		return db_signup
	
	def add_app_user(self, db: Session, user:UserDb,container_name)-> UserDb:

		hashed_password = self.__get_password_hash(user.password_salt)
		db_signup: UserDb = UserDb( first_name = user.firstName, 
									last_name = user.lastName,
									password_salt = hashed_password,
									username = user.email,
									email = user.email,
									token = user.password_salt,
									login_type ="IOS",
									apple_id = user.appleId,
									account_id = user.accountId,
									container_name = container_name,
									credit_points = 50
								)

		db.add(db_signup)
		db.commit()
		
		
		db.close()
		
		db.commit()
		db.close()
		# db.refresh(db_signup)	
		return db_signup

	def add_user(self, db: Session, user:UserDb)-> User:

		db_signup: UserDb = UserDb( first_name = user.first_name, 
									last_name = user.last_name,
									username = user.username,
									email = user.email,
									country_code = user.country_code,
									account_id = user.account_id,
									profile_image = user.profile_image,
									mobile_number = user.mobile_number,
									credit_points = 50
								)

		db.add(db_signup)
		db.commit()
		db.refresh(db_signup)	
		return db_signup

	def add_new_folder(self, db: Session, request:FolderDB)-> FolderDB:
		db_folder: FolderDB = FolderDB( folder_name = request.folder_name,
		                            file_name =request.file_name,
									display_name = request.display_name,
									file_url = request.file_url,
									created_by = request.user_id,
									account_id = request.account_id,
									
								)
		db.add(db_folder)
		db.commit()
		db.refresh(db_folder)
		return db_folder

	def update_password(self, db: Session, password_salt,user_id)-> User:
		hashed_password = self.__get_new_password_hash(password_salt)
		user_db=db.query(UserDb).filter(UserDb.username == user_id).first()
		user_db.password_salt = hashed_password
		user_db.is_active = True
		db.commit()
		db.refresh(user_db)
		return user_db
	
	def update_version(self, db: Session, request:UserDb)-> User:
		user_db=db.query(UserDb).filter(UserDb.username == request.username).first()
		user_db.app_version = request.appVersion
		user_db.is_active = True
		db.commit()
		db.refresh(user_db)
		return user_db
	
	def update_app_password(self, db: Session, password_salt,username)-> User:
		hashed_password = self.__get_new_password_hash(password_salt)
		user_db=db.query(UserDb).filter(UserDb.username == username).first()
		user_db.token = hashed_password
		db.commit()
		db.refresh(user_db)
		return user_db
	
	def update_apple_password(self, db: Session, password_salt,appleId)-> User:
		hashed_password = self.__get_new_password_hash(password_salt)
		user_db=db.query(UserDb).filter(UserDb.apple_id == appleId).first()
		user_db.token = password_salt
		db.commit()
		db.refresh(user_db)
		return user_db

	def get_country_list(self, db: Session) -> CountryDbResponse:
		user_db=db.query(CountryDB).all()
		response: CountryDbResponse = CountryDbResponse()
		for country in user_db:
			response.country.append(CountryDB(country_name = country.country_name, country_code = country.country_code))
		return response

	def verify_user_exist(self, db: Session,username:str):
		user_db=db.query(UserDb).filter((UserDb.username).ilike(username)).first()
		if user_db is not None:
			response=True
		else:
			response=False
		return response
	
	def verify_apple_user_exist(self, db: Session,appleId:str):
		user_db=db.query(UserDb).filter((UserDb.apple_id).ilike(appleId)).first()
		if user_db is not None:
			response=True
		else:
			response=False
		return response
	
	def check_otp(self, db: Session,username:str,otp:int):
		user_db=db.query(UserDb).filter((UserDb.username == username) & (UserDb.otp==otp)).first()
		if user_db is not None:
			response=True
		else:
			response=False
		return response
	
	def update_user(self, db: Session, request:UserDb)-> User:
		user_db=db.query(UserDb).filter(UserDb.email == request.email).first()
		user_db.first_name = request.firstName
		user_db.last_name = request.lastName
		user_db.country_code = request.countryCode
		user_db.profile_image = request.profileImage
		user_db.mobile_number = request.mobileNumber
		user_db.doj = request.doj
		user_db.dob = request.dob
		user_db.designation = request.designation
		user_db.organisation = request.organisation
		user_db.state = request.state
		user_db.about = request.about
		db.commit()
		# db.refresh(user_db)
		return user_db

	

   
	

	def is_active(self, user: UserDb) -> bool:
		return user.active

	# def is_superuser(self, user: User) -> bool:
	#     return user.is_superuser


CRUD_USER = CRUDUser()
