from datetime import datetime, timedelta
from importlib.util import resolve_name
from typing import Any, Callable, Union

from fastapi import FastAPI
from ...core import AppSettings
from jose import jwt
from passlib.context import CryptContext
from ..schemas import Token
from abc import *

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ISecurityService():
	@abstractmethod
	def create_access_token(subject: str, expires_delta: timedelta = None ) -> Token:
		pass
	
	@abstractmethod    
	def verify_password(self,plain_password: str, hashed_password: str) -> bool:
		pass

	@abstractmethod
	def get_password_hash(password: str) -> str:
		pass

	@abstractmethod
	def update_schema_name(self,app: FastAPI, function: Callable, name: str) -> str:
		pass
		   

class SecurityService(ISecurityService):

	
	def create_access_token(self,subject: str, expires_delta: timedelta = None ) -> Token:
		if expires_delta:
			expire = datetime.utcnow() + expires_delta
		else:
			expire = datetime.utcnow() + timedelta(
				minutes=AppSettings.API.ACCESS_TOKEN_EXPIRE_MINUTES
			)
		to_encode = {"exp": expire, "sub": str(subject)}
		encoded_jwt = jwt.encode(to_encode, AppSettings.API.SECRET_KEY, algorithm=AppSettings.API.ALGORITHM)
		response = Token()
		response.token_type= "bearer"
		response.access_token=encoded_jwt
		return response


	def verify_password(self,plain_password: str, hashed_password: str) -> bool:
		return PWD_CONTEXT.verify(plain_password, hashed_password)

	def get_password_hash(password: str) -> str:
		return PWD_CONTEXT.hash(password)

	def update_schema_name(self,app: FastAPI, function: Callable, name: str) -> None:
		for route in app.routes:
			
			if route.endpoint is function:
				route.body_field.type_.__name__ = name
				break


SECURITY_SERVICE:ISecurityService = SecurityService()