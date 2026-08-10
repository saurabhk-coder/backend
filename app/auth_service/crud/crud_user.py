from datetime import date, timedelta
from typing import Any, Dict, Optional,List
import bcrypt
from sqlalchemy.orm import Session
from psycopg2 import errors

from app.user_service.schemas.user import UserListResponse
from ..models import *
from ..schemas import User,CountryDbResponse
from passlib.context import CryptContext
UniqueViolation = errors.lookup('23505')



class CRUDUser():
	def __init__(self):
		self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

	def __get_password_hash(self, password: str):
		return self.pwd_context.hash(password[0])
   
	def get_by_email(self, db: Session,  email: str) -> Optional[UserDb]:
		return db.query(UserDb).filter((UserDb.email).ilike(email)).first()

	def get_user_byid(self, db: Session,  id: int) -> Optional[UserDb]:
		return db.query(UserDb).filter(UserDb.user_id == id).first()

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

	def add_new_user(self, db: Session, user:UserDb,container_name)-> UserDb:

		hashed_password = self.__get_password_hash(user.password_salt)
		db_signup: UserDb = UserDb( first_name = user.firstName, 
									last_name = user.lastName,
									password_salt = hashed_password,
									username = user.username,
									email = user.email,
									# country_code = user.countryCode,
									account_id = user.accountId,
									container_name = container_name
								)

		db.add(db_signup)
		db.commit()
		db_client: ClientDB = ClientDB( client_name = "Default Client", 
										created_by = db_signup.user_id,
										account_id = db_signup.account_id,
										contact_number = "",
										email = "",
										logo_image = "",
										website = "",
										about = "",
										
									)
		db.add(db_client)
		db.commit()
		db_client: ClientDB = ClientDB( client_name = "Default Client", 
										created_by = db_signup.user_id,
										account_id = db_signup.account_id
									)
		db.add(db_client)
		db.commit()
		db_project: ProjectDB = ProjectDB( project_name = "Demo D", 
									client_id = db_client.client_id,
									project_description = "Demo Project",
									project_type = "Hospitality",
									created_by = db_signup.user_id,
									account_id = db_signup.account_id,
									flag = 0,
									status=1,
									due_date = date.today()+timedelta(days=30),
									address = "",
									contact = "",
									contact_point = "",
									start_date = date.today()+timedelta(days=30),
									end_date = date.today()+timedelta(days=30),
									project_image = ""
									
									
								)
		db.add(db_project)
		db.commit()
		

		db_test: ProjectTeamDB = ProjectTeamDB(
						user_id=db_signup.user_id,
						account_id=db_signup.account_id,
						project_id = db_project.project_id,
						role = 1,
						status = 1,
						created_by = db_signup.user_id,
			        )
		
		db.add(db_test)
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
									mobile_number = user.mobile_number
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

	def update_password(self, db: Session, password_salt,username)-> User:
		pwhash = bcrypt.hashpw(str(password_salt).encode(encoding='UTF-8',errors='strict'), bcrypt.gensalt())
		password_hash = (pwhash.decode('utf8')).replace('$2b','$2a')
		user_db=db.query(UserDb).filter(UserDb.email == username).first()
		user_db.password_salt = password_hash
		db.commit()
		db.refresh(user_db)
		return user_db

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

	def get_country_list(self, db: Session) -> CountryDbResponse:
		user_db=db.query(CountryDB).all()
		# response: CountryDbResponse = CountryDbResponse()
		# for country in user_db:
		# 	response.country.append(CountryDB(country_name = country.country_name, country_code = country.country_code))
		return user_db

	def get_user_list(self, db: Session,account_id: str) -> List[UserDb]:
		return db.query(UserDb).filter(UserDb.account_id == account_id).all()

	def get_user_list_name(self, db: Session,first_name:str,account_id: str) -> List[UserDb]:
		return db.query(UserDb).where(UserDb.account_id==account_id or UserDb.first_name.like("%"+first_name + "%")).all()

	

	def verify_user_exist(self, db: Session,username:str):
		user_db=db.query(UserDb).filter(UserDb.username == username).first()
		if user_db is not None:
			response=True
		else:
			response=False
		return response

	

   
	

	def is_active(self, user: UserDb) -> bool:
		return user.active

	# def is_superuser(self, user: User) -> bool:
	#     return user.is_superuser


CRUD_USER = CRUDUser()
