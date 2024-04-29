from datetime import datetime
import shutil
import os
import time
import json

from typing import List, Type
from dotenv import load_dotenv

# helpers, libraries
from typing import List, Type
from dotenv import load_dotenv
from app.helpers.definitions import get_directory_path
from app.helpers.s3_file_upload import upload_image_to_s3

# tortoise
from tortoise.contrib.fastapi import HTTPNotFoundError

# fastapi
from fastapi import APIRouter, Depends, status, Request, HTTPException, File, UploadFile, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

# models
from app.models.interviewee import interviewee_pydantic, Interviewee
# from app.models.user_schema import CreateUser, CreateUserToken, ChangeUserPassword, UpdateUserInfo

# authentication
from app.auth.authentication import hash_password, token_generator, verify_password, verify_token_interviewee_email

from app.helpers.s3_file_upload import upload_file_to_s3, generate_s3_url

# email user verification
# from app.auth.email_verification import send_email

# mailer
from app.helpers.mailer import Mailer, EmailSchema

# pydantic interviewee schema
from app.models.interviewee_schema import Interviewee as IntervieweeSchema

# s3 bucket directories
s3_interviewee_image_upload_folder = 'uploads/interview/img/'
s3_interviewee_rcimage_upload_folder = 'uploads/interview/cardimg/'

router = APIRouter(
    prefix="/interviewees",
    tags=["Interviewees"],
)

load_dotenv()

upload_path = get_directory_path() + '\\uploads'


@router.get("", name="Get all interviewees")
async def get_interviewees():
    return await interviewee_pydantic.from_queryset(Interviewee.all())


def create_email_body(interviewee):
    interview_dates_html = ''.join([
        f"<li>{date['date']} at {date['time']}</li>"
        for date in interviewee['selected_dates']
    ])

    return f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1, h2 {{ color: #333366; }}
                p {{ margin: 10px 0; }}
                ul {{ list-style-type: none; padding: 0; }}
                li {{ margin: 5px 0; }}
                img {{ max-width: 100%; height: auto; max-width: 400px; }}
            </style>
        </head>
        <body>
            <h1>エンジェルケアサービスのアルバイト募集</h1>
            <p>新しい面接の申し込みを受け取りました。</p>
            <h2>応募者情報</h2>
            <p><strong>名前:</strong> {interviewee['first_name']} {interviewee.get('middle_name', '')} {interviewee['last_name']}</p>
            <p><strong>大学名:</strong> {interviewee['university_name']}</p>
            <p><strong>電子メール:</strong> {interviewee['email']}</p>
            <p><strong>面接日時:</strong></p>
            <ul>{interview_dates_html}</ul>
            <p><strong>応募日:</strong> {interviewee['birth_date']}</p>
            <p><strong>在留カード番号:</strong> {interviewee['residence_card_number']}</p>
            
            <p><strong>電話番号:</strong> {interviewee['phone_number']}</p>
            <img src="{interviewee['img_url']}" alt="Applicant Image">

            <hr>
            <h1>Recruitment of Part-time Workers at Angel Care Services</h1>
            <p>A new application for an interview has been received.</p>
            <h2>Applicant Information</h2>
            <p><strong>Name:</strong> {interviewee['first_name']} {interviewee.get('middle_name', '')} {interviewee['last_name']}</p>
            <p><strong>University:</strong> {interviewee['university_name']}</p>
            <p><strong>Email:</strong> {interviewee['email']}</p>
            <p><strong>Interview Dates:</strong></p>
            <ul>{interview_dates_html}</ul>
            <p><strong>Application Date:</strong> {interviewee['birth_date']}</p>
            <p><strong>Residence Card Number:</strong> {interviewee['residence_card_number']}</p>
            
            <p><strong>Phone Number:</strong> {interviewee['phone_number']}</p>
            <img src="{interviewee['residence_card_image']}" alt="Residence Card Image">
        </body>
    </html>
    """


def create_management_notification_message(interviewee):
    name = f"{interviewee['first_name']} {interviewee.get('middle_name', '')} {interviewee['last_name']}".strip(
    )
    interview_date = interviewee['selected_dates'][0]['date']
    interview_time = interviewee['selected_dates'][0]['time']
    phone_number = interviewee['phone_number']

    message = (
        f"こんにちは {name}さん、\n"
        f"エンジェルケアサービスへの新しい面接申し込みがありました。詳細は自分のLINEWORKSのメールで確認してください。\n"
        f"確認して、適切な対応をお願いします。連絡先: {phone_number}\n\n"
        f"Hello {name},\n"
        f"You have received a new interview application for a part-time job at Angel Care Services. "
        f"Details can be viewed at your line works email. "
        f"Please confirm and proceed accordingly. Contact: {phone_number}"
    )
    return message


@router.post("/register_interviewee", name="Create interviewee")
async def save_interviewee(data_json: str = Form(...), interviewee_image: UploadFile = File(None), residence_card_image: UploadFile = File(None)):
    try:
        details = json.loads(data_json)
        print("Interviewee json data: ", details)
    except json.JSONDecodeError as e:
        print("Interviewee Data Incorrect JSON Format: ", str(e))
        return JSONResponse(content={"Interviewee Data Incorrect JSON Format": str(e)}, status_code=400)

    # residence_card_number is unique, if it already exists, return an error
    residence_card_number = details['residence_card_number']
    exists = await Interviewee.filter(residence_card_number=residence_card_number).exists()
    if exists:
        raise HTTPException(
            status_code=400, detail="Residence card number already exists.")

    now = datetime.now()

    if interviewee_image:
        image_name = details['first_name'] + \
            details['last_name'] + '_dp_' + \
            now.strftime("_%Y%m%d_%H%M%S") + ".jpg"

        upload_file_to_s3(interviewee_image, image_name,
                          s3_interviewee_image_upload_folder)

        s3_img_path = s3_interviewee_image_upload_folder + image_name

        s3_read_url = generate_s3_url(s3_img_path, 'read')

        details['img_url'] = s3_read_url
        print("Interviewee image uploaded successfully.")

    if residence_card_image:
        image_name = details['first_name'] + \
            details['last_name'] + '_residencecard_' + \
            now.strftime("_%Y%m%d_%H%M%S") + ".jpg"

        upload_file_to_s3(residence_card_image, image_name,
                          s3_interviewee_rcimage_upload_folder)

        s3_img_path = s3_interviewee_image_upload_folder + image_name

        s3_read_url = generate_s3_url(s3_img_path, 'read')

        details['residence_card_image'] = s3_read_url
        print("Residence card image uploaded successfully.")

    # save the interviewee
    interviewee = await Interviewee.create(**details)

    new_interviwee = await interviewee_pydantic.from_tortoise_orm(interviewee)

    # new interviewee print saved details
    print("New Interviewee: ", new_interviwee)

    # send mail
    mailer = Mailer()

    msg_body = create_email_body(details)

    sms_body = create_management_notification_message(details)

    mail_details = EmailSchema(
        email=[details['email'], "kazuhiro110@makeyousmile.jp"],
        body=msg_body,
        subject="エンジェルケアサービス アルバイト面談申し込みフォーム | Angel Care Services Part-time Job Recruitment Application"
    )

    try:
        await mailer.send_email(mail_details)
        print("Email sent successfully.")

    except Exception as e:
        print("Email sending failed: ", str(e))

    try:
        sms = await mailer.send_sms(
            # "080-3173-9868",
            "+818031739868",
            sms_body)

        print(sms)

        # send also for sender for application confirmation
        # sms = await mailer.send_sms(
        #     details['phone_number'],
        #     sms_body)

        print("SMS sent successfully.")
    except Exception as e:
        print("SMS sending failed: ", str(e))

    return new_interviwee


@router.get("/get_interviewee_info", name="Get interviewee info")
async def get_interviewee_info(token: str):
    # token = await token_generator('millanjarvis421@gmail.com', 'Sivrajnallim96')
    interviewee = await verify_token_interviewee_email(token)

    if not interviewee:
        # Raise a 401 Unauthorized error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or Expired token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return interviewee


@router.get("/{email}", name="Get interviewee by email", responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}})
async def read_user(email: str):
    return await interviewee_pydantic.from_queryset_single(Interviewee.get(email=email))


@router.get("/verification", name="Verify Interviewee", responses={status.HTTP_404_NOT_FOUND: {"model": HTTPNotFoundError}})
async def verify_interviewee(token: str):  # request: Request,
    interviewee = await verify_token_interviewee_email(token)
    print("user object ", interviewee)
    if interviewee:
        if not interviewee.is_verified:
            interviewee.is_verified = True
            # await User.filter(id=user.id).update()
            await interviewee.save()
            return {"msg": "interviewee successfully verified."}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or Expired token.",
        headers={"WWW-Authenticate": "Bearer"}
    )
