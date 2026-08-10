from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DefaultClause, text
from ..db import Base



class UsersDb(Base):
	__tablename__ = "users"
	__table_args__ = {'extend_existing': True} 
	id = Column(UUID, primary_key=True, server_default=DefaultClause(text("gen_random_uuid()")))
	username = Column(String, unique=True, index=True)
	email= Column(String, unique=True, index=True)
	password_salt= Column(String,  nullable=True)
	first_name= Column(String,  nullable=True)
	last_name=Column(String,   nullable=True)
	country_code= Column(String,  nullable=False)
	profile_image= Column(String,  nullable=True)
	is_active = Column(Boolean(), default=True)
	is_verified=Column(Boolean(), default=False)
	created_at= Column(String, default=datetime.utcnow())
	updated_at= Column(String, nullable=True)
	created_by= Column(String, nullable=True)
	updated_by= Column(String, nullable=True)
	app_version= Column(String, nullable=True)

class CountryDB(Base):
	__tablename__ = "country"

	id = Column(Integer, primary_key=True, index=True, autoincrement=True)
	country_name = Column(String, unique=True, index=True)
	country_code= Column(String, unique=True, index=True)