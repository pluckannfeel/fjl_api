from json import JSONEncoder, JSONDecoder
from uuid import UUID

from typing import Type

from app.models.user import User

from fastapi import Depends, HTTPException, status, Security, Response, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# async def get_user_by_username(input_username: str) -> user_pydantic:
#     return await user_pydantic.from_queryset_single(User.get(username=input_username))


class UUIDEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the ob is uuid,
            return str(obj)
        return JSONEncoder.default(self, obj)


class UUIDDecoder(JSONDecoder):
    def decode(self, obj):
        return JSONDecoder.decode(self, obj)


class AuthenticationManager():
    def __init__(self):
        self.security = HTTPBasic()

    def verify_credentials(self, username: str, password: str):
        correct_username = "admin"
        correct_password = "secret"
        if username == correct_username and password == correct_password:
            return True
        return False