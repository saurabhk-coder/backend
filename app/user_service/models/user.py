from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, DefaultClause, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import synonym
from ..db import Base



class UsersDb(Base):
	__tablename__ = "users"
	__table_args__ = {"schema": "hrms", "extend_existing": True}
	id = Column(UUID(as_uuid=True), primary_key=True, server_default=DefaultClause(text("gen_random_uuid()")))
	organization_id = Column(UUID(as_uuid=True), index=True, nullable=True)
	role_id = Column(UUID(as_uuid=True), index=True, nullable=True)
	email = Column(String, unique=True, index=True)
	password_salt = Column(String, nullable=True)
	password_hash = synonym("password_salt")
	first_name = Column(String, nullable=True)
	last_name = Column(String, nullable=True)
	country_code = Column(String, nullable=True)
	status = Column(String, nullable=True)
	is_active = Column(Boolean, nullable=True, default=False)
	created_at = Column(DateTime, default=datetime.utcnow)
	updated_at = Column(DateTime, nullable=True)

class CountryDB(Base):
	__tablename__ = "country"

	id = Column(Integer, primary_key=True, index=True, autoincrement=True)
	country_name = Column(String, unique=True, index=True)
	country_code= Column(String, unique=True, index=True)