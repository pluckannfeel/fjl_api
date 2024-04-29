from typing import List
from dotenv import dotenv_values
from app.models.email_schema import VerificationEmail
from app.models.user import User
import jwt
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi_mail.errors import ConnectionErrors
from fastapi import BackgroundTasks, UploadFile, File, Form, Depends, HTTPException, status

# uuid json serialize
import json
from app.helpers.user import UUIDEncoder

# send grid
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# config_credentials
env_credentials = dotenv_values('.env')


async def send_email(emails: List, user: User):
    token_data = {
        "id": json.dumps(user.id, cls=UUIDEncoder),
        "username": user.email
    }

    token = jwt.encode(token_data, env_credentials["SECRET_KEY"])

    template = f"""
        <!DOCTYPE html>
        <html>
            <head>
            </head>
            <body>
                <div style = "display: flex; align-items: center; justify-content:
                                center; flex-direction: column">
                    <h3> Account Verificcation </h3>
                    <br>
                    <p> Thank you, please click on link </p>
                    <a href="http://localhost:8000/users/verification/?token={token}">Verify</a>
                </div>
            </body>
        </html>
        
        
    """

    message = Mail(
        from_email=env_credentials['MAIL_USERNAME'],
        to_emails=emails,
        subject='Verify User Registration',
        html_content=template
    )

    try:
        sg = SendGridAPIClient(env_credentials['SENDGRID_API_KEY'])
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)