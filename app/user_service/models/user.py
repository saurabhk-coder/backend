from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DefaultClause, text
from ..db import Base



class UsersDb(Base):
	__tablename__ = "users"
	__table_args__ = {"schema": "hrms"}
	id = Column(UUID, primary_key=True, server_default=DefaultClause(text("gen_random_uuid()")))
	organization_id = Column(UUID,  index=True)
	role_id = Column(UUID,  index=True)
	email= Column(String, unique=True, index=True)
	password_hash= Column(String,  nullable=True)
	first_name= Column(String,  nullable=True)
	last_name=Column(String,   nullable=True)
	country_code= Column(String,  nullable=False)
	status= Column(String,  nullable=True)
	created_at= Column(String, default=datetime.utcnow())
	updated_at= Column(String, nullable=True)

class CountryDB(Base):
	__tablename__ = "country"

	id = Column(Integer, primary_key=True, index=True, autoincrement=True)
	country_name = Column(String, unique=True, index=True)
	country_code= Column(String, unique=True, index=True)