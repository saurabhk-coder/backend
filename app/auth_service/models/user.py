from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DefaultClause, text
from ..db import Base



class UserDb(Base):
	__tablename__ = "users"
	__table_args__ = {'extend_existing': True} 
	id = Column(UUID, primary_key=True, server_default=DefaultClause(text("gen_random_uuid()")))
	organization_id = Column(UUID,  index=True)
	role_id = Column(UUID,  index=True)
	email= Column(String, unique=True, index=True)
	password_salt= Column(String,  nullable=True)
	first_name= Column(String,  nullable=True)
	last_name=Column(String,   nullable=True)
	country_code= Column(String,  nullable=False)
	status= Column(String,  nullable=True)
	created_at= Column(String, default=datetime.utcnow())
	updated_at= Column(String, nullable=True)
	is_active= Column(String, nullable=True)

class AccountDb(Base):
	__tablename__ = "accounts"
	id = Column(UUID, primary_key=True, server_default=DefaultClause(text("gen_random_uuid()")))
	account_name = Column(String, unique=True, index=True)
	created_at= Column(String, default=datetime.utcnow())
	

class CountryDB(Base):
	__tablename__ = "lst_country"

	id = Column(Integer, primary_key=True, index=True, autoincrement=True)
	country_name = Column(String, unique=True, index=True)
	country_code= Column(String, unique=True, index=True)

class FolderDB(Base):
	__tablename__ = "file_folder"
	__table_args__ = {'extend_existing': True} 
	folder_id = Column(UUID, primary_key=True, server_default=DefaultClause(text("gen_random_uuid()")))
	folder_name= Column(String,  nullable=True)
	file_id= Column(UUID,  nullable=True)
	file_name= Column(String,  nullable=True)
	file_size= Column(String,  nullable=True)
	content_type= Column(String,  nullable=True)
	file_url= Column(String,  nullable=True)
	file_extension= Column(String,  nullable=True)
	storage_file_name=Column(String,  nullable=True)
	created_by= Column(UUID,  nullable=True)
	updated_by= Column(String,  nullable=True)
	created_at= Column(String, default=datetime.utcnow())
	updated_at= Column(String, nullable=True)
	account_id= Column(UUID,  nullable=True)
	display_name= Column(String, nullable=True)