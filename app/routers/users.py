import os
import json

from dotenv import load_dotenv
from app.helpers.definitions import get_directory_path
from app.helpers.s3_file_upload import upload_file_to_s3

from tortoise.contrib.fastapi import HTTPNotFoundError

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form

from app.models.user import User, user_pydantic
from app.models.user_schema import CreateUser, CreateUserToken, ChangeUserPassword

from app.auth.authentication import hash_password, token_generator, verify_password, verify_token_email


router = APIRouter(
    prefix="/users",
    tags=["users"],
)

load_dotenv()

upload_path = get_directory_path() + "\\uploads"
s3_upload_path = str(os.getenv("AWS_STORAGE_BUCKET_NAME")) + 'uploads'


@router.get("/get_user_info", name="Get User Info")
async def get_user_info(token: str):
    user = await verify_token_email(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or Expired token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


@router.get("/{email}", name="Get user by email", responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}})
async def read_user(email: str):
    # return await user_pydantic.from_queryset_single(User.get(email=email))
    # get user credentials by email
    user_info = await User.get(email=email).values(
        'id', 'first_name', 'last_name', 'email', 'phone', 'job', 'role', 'created_at', 'is_verified'
    )

    return user_info


@router.get("/verification", name="Verify User", responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}})
async def verify_user(token: str):  # request: Request,
    user = await verify_token_email(token)
    print("user object ", user)
    if user:
        if not user.is_verified:
            user.is_verified = True
            # await User.filter(id=user.id).update()
            await user.save()
            return {"msg": "user successfully verified."}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or Expired token.",
        headers={"WWW-Authenticate": "Bearer"}
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, name="Create User")
async def create_user(user: CreateUser):
    user_info = user.dict(exclude_unset=True)

    # check if email already exists
    if await User.filter(email=user_info['email']).exists():
        raise HTTPException(
            status_code=401,
            detail="email_exists",
            headers={'WWW-Authenticate': 'Bearer'}
        )

    # check if invite code is valid
    invitation_code = "Makeyousmile2018"
    if user_info['invitation_code'] != invitation_code:
        raise HTTPException(
            status_code=401,
            detail="invalid_invitation_code",
            headers={'WWW-Authenticate': 'Bearer'}
        )

    user_data = await User.create(
        first_name=user_info['first_name'], last_name=user_info['last_name'],
        #   birth_date=user_info['birth_date'],
        #   username=user_info['username'],
        email=user_info['email'],
        # phone=user_info['phone'],
        role=user_info['role'],
        password_hash=hash_password(user_info['password'].get_secret_value()))
    # user_obj = await User.create(**user_info)

    new_user = await user_pydantic.from_tortoise_orm(user_data)

    emails = [new_user.email]

    # if new_user:
    #     print("New user: " + new_user.email)
    #     # for sending email verification
    #     await send_email(emails, new_user)

    return {'user': new_user, 'msg': "new user created."}


@router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(login_info: CreateUserToken) -> dict:
    token = await token_generator(login_info.email, login_info.password)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="invalid_credentials",
            headers={'WWW-Authenticate': 'Bearer'}
        )

    return {'token': token, 'email': login_info.email, 'msg': "user logged in."}


@router.put('/update_user_info', status_code=status.HTTP_200_OK, )
async def update_user(user_json: str = Form(...)):
    # Parse the JSON string into a dictionary
    user_data = json.loads(user_json)

    # remove id from the dictionary
    user_id = user_data.pop('id')

    # get user email from id
    user_email = await User.get(id=user_id).values('email')

    # check if the current user is the same as the email entered
    if user_data['email'] == user_email:
        # if user email input matched with the current user email
        # update User without email
        await User.filter(id=user_id).update(
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            phone=user_data['phone'],
            job=user_data['job'],
            role=user_data['role']
        )
    else:
        await User.filter(id=user_id).update(**user_data)

    # get the new updated user info
    updated_user_info = await User.get(id=user_id).values('id', 'first_name', 'last_name', 'email', 'phone', 'job', 'role', 'created_at')

    return updated_user_info


@router.put("/change_password", status_code=status.HTTP_200_OK)
async def change_user_password(user_info: ChangeUserPassword) -> dict:
    user = await User.get(email=user_info.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    old_password = user_info.old_password.get_secret_value()

    if not await verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user.password_hash = hash_password(
        user_info.new_password.get_secret_value())
    await user.save()

    return {'msg': "Password successfully changed."}
