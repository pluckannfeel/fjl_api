from datetime import date
from pydantic import BaseModel, EmailStr, SecretStr, root_validator
# import email_validator

from app.auth.authentication import authenticate_user, verify_password


class CreateUser(BaseModel):
    first_name: str
    last_name: str
    # username: str
    # birth_date: date
    email: EmailStr
    # phone: str
    # job: str
    role: str
    invitation_code: str
    password: SecretStr
    # confirm_password: SecretStr

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

    @root_validator(pre=True)
    def user_validator(cls, values):
        # check values if there is one null
        for value in values:
            if len(values.get(value)) == 0:
                raise ValueError('Form has an empty field.')

        # check if password and confirm password not matches
        # password, confirm = values.get('password_hash'), values.get('confirm_password')
        # if password != confirm:
        #     raise ValueError('password and confirm password does not match.')

        return values


class CreateUserToken(BaseModel):
    email: EmailStr
    password: str

    @root_validator(pre=True)
    def user_validator(cls, values):
        # check values if there is one null
        for value in values:
            if len(values.get(value)) == 0:
                raise ValueError('Form has an empty field.')

        # username, password = values.get('username'), values.get('password')
        # if not password_hash_context.verify(username, password):
        #     raise ValueError('Username and/or password is invalid.')

        return values


class ChangeUserPassword(BaseModel):
    email: EmailStr
    old_password: SecretStr
    new_password: SecretStr

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

    @root_validator(pre=True)
    def user_validator(cls, values):
        # check values if there is one null
        for value in values:
            if len(values.get(value)) == 0:
                raise ValueError('Form has an empty field.')

        # check if password and confirm password not matches
        # password, confirm = values.get('new_password'), values.get('confirm_password')
        # if password != confirm:
        #     raise ValueError('password and confirm password does not match.')

        return values


class UpdateUserInfo(BaseModel):
    # id: str
    # user_email: EmailStr
    first_name: str
    last_name: str
    email: EmailStr
    job: str
    phone: str
    role: str

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

    # @root_validator(pre=True)
    # def user_validator(cls, values):
    #     # check values if there is one null
    #     for value in values:
    #         if len(values.get(value)) == 0:
    #             raise ValueError('Form has an empty field.')
