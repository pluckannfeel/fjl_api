from fastapi import FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Union

# database
from app.db.init import initialize_db

from mangum import Mangum

from app.routers.users import router as userRouter
from app.routers.applicant import router as applicantRouter
from app.routers.interviewees import router as intervieweeRouter

# mailing
from app.helpers.mailer import Mailer, EmailSchema


app = FastAPI(title="FJL API", version="1.0",
              description="Philippine Jinzai Kaihatsu Lab API")

oauth_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

initialize_db(app)

origins = [
    '*',
    # 'http://localhost',
    # 'http://localhost:3000',
    # 'http://localhost:8000',
    # 'http://localhost:8080',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

# routers
app.include_router(userRouter)
app.include_router(applicantRouter)
app.include_router(intervieweeRouter)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/send_mail_by_guest")
async def send_mail_by_guest(email: str, name: str, message: str):
    try:

        body = f"""
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
                        <h1>FJLから新しいメッセージを受け取りました</h1>
                        <p><strong>名前:</strong> {name}</p>
                        <p><strong>メールアドレス:</strong> {email}</p>
                        <p><strong>メッセージ内容:</strong> {message}</p>
                        
                        <p><strong>https://www.fjl.jp/</strong></p>
                    </body>
                </html>
                """

        mailer = Mailer()

        details = EmailSchema(
            email=["dev@makeyousmile.jp"],
            body=body,
            subject="FJLから新しいメッセージを受け取りました"
        )

        await mailer.send_email(details)

        return {"message": "email has been sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/send_mail")
async def send_mail(recipient_email: str, subject: str, body: str):
    try:

        mailer = Mailer()

        details = EmailSchema(
            email=[recipient_email],
            body=body,
            subject=subject
        )

        await mailer.send_email(details)

        return {"message": "email has been sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


handler = Mangum(app)
