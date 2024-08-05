from tortoise.contrib.fastapi import register_tortoise
from dotenv import load_dotenv
import os

load_dotenv()

db_uri = os.environ['DB_URI']


def initialize_db(app):
    # print("DB_URI: ", db_uri)
    register_tortoise(
        app,
        # db_url='postgres://postgres:admin@localhost:5432/mys_db',# local postgres
        # db_url='postgres://postgres:admin@postgresql/kaisha_db', #docker pgadmin
        db_url=db_uri,
        modules={
            'models': [
                'app.models.user',
                'app.models.organization',
                'app.models.applicant',
                'app.models.interviewee',
                'app.models.company',
                'app.models.agency'
            ]
        },
        generate_schemas=True,
        add_exception_handlers=True
    )
    print('db initialized')
