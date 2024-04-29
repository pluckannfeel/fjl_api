from fastapi import FastAPI, Form, HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from typing import List
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import boto3

from concurrent.futures import ThreadPoolExecutor
import asyncio

load_dotenv()

access_key = os.environ["AWS_ACCESS_KEYID"]
secret_access_key = os.environ["AWS_SECRET_ACCESSKEY"]


class EmailSchema(BaseModel):
    email: List[EmailStr]
    body: str
    subject: str


class Mailer:
    def __init__(self):
        self.config = ConnectionConfig(
            MAIL_USERNAME="jarvis@makeyousmile.jp",
            MAIL_PASSWORD="nDL2ZM62DM8c",
            # MAIL_PASSWORD="@Sivrajnallim96",
            MAIL_FROM="jarvis@makeyousmile.jp",
            # SMTP port for STARTTLS (replace with 465 if using SSL/TLS directly)
            MAIL_PORT=587,
            # SMTP server address (replace with actual SMTP server)
            MAIL_SERVER="smtp.worksmobile.com",
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,  # Set based on your server's requirements
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=False  # Be cautious with disabling certificate validation in production
        )

    async def send_sms(self, phone_number: str, message: str):
        sns_session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_access_key,
            region_name="ap-northeast-1"
        )
        sns_client = sns_session.client("sns")

        # Define a function to run the blocking operation in a thread
        def publish_sms():
            return sns_client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )

        # Use ThreadPoolExecutor to execute the blocking function asynchronously
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            response = await loop.run_in_executor(pool, publish_sms)
            return response

        # # check if the message was sent
        # return {"message": "SMS sent successfully"}

    async def send_email(self, email: EmailSchema):
        message = MessageSchema(
            subject=email.subject,
            recipients=email.email,  # List of recipients, as per Pydantic model
            body=email.body,
            subtype="html"
        )
        fm = FastMail(self.config)
        await fm.send_message(message)
        return {"message": "Mail sent successfully"}
