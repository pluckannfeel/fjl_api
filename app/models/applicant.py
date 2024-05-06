from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator


class Applicant(Model):
    id = fields.UUIDField(pk=True, index=True)
    organization = fields.ForeignKeyField(
        'models.Organization', related_name='applicants', null=True)
    img_url = fields.TextField(null=True)
    first_name = fields.CharField(max_length=255, null=False)
    last_name = fields.CharField(max_length=255, null=False)
    middle_name = fields.CharField(max_length=255, null=True)
    birth_date = fields.DateField(null=True)
    age = fields.IntField(null=True)
    gender = fields.CharField(max_length=50, null=True)
    nationality = fields.CharField(max_length=50, null=True)
    birth_place = fields.CharField(max_length=255, null=True)
    marital_status = fields.CharField(max_length=50, null=True)
    occupation = fields.CharField(max_length=255, null=True)
    current_address = fields.TextField(null=True)
    phone_number = fields.CharField(max_length=255, null=True)
    # legal docs
    passport_number = fields.CharField(max_length=255, null=True)
    passport_expiry = fields.DateField(null=True)
    email = fields.CharField(max_length=255, null=True)
    password_hash = fields.CharField(max_length=128, null=True)
    family = fields.TextField(null=True)
    education = fields.TextField(null=True)
    work_experience = fields.TextField(null=True)
    qualifications_licenses = fields.TextField(null=True)
    jlpt = fields.CharField(max_length=20, null=True)
    jft = fields.CharField(max_length=20, null=True)
    nat = fields.CharField(max_length=20, null=True)
    japanese = fields.CharField(max_length=50, null=True)
    english = fields.CharField(max_length=50, null=True)
    computer_skills = fields.TextField(null=True)
    other_skills = fields.TextField(null=True)
    self_introduction = fields.TextField(null=True)
    reason_for_application = fields.TextField(null=True)
    past_experience = fields.TextField(null=True)
    future_career_plan = fields.TextField(null=True)
    photos = fields.TextField(null=True)
    links = fields.TextField(null=True)
    unique_questions = fields.TextField(null=True)
    required_questions = fields.TextField(null=True)
    recruiter = fields.CharField(max_length=255, null=True)
    organization = fields.CharField(max_length=255, null=True)
    visa = fields.CharField(max_length=255, null=True)
    interview_date = fields.DateField(null=True)
    result = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)


applicant_pydantic = pydantic_model_creator(
    Applicant, name="Applicant",
    exclude=(
        "password_hash",
        "links",
        # "unique_questions", "required_questions", "photos",
        # "future_career_plan", "past_experience", "reason_for_application", "self_introduction",
        # "english", "japanese", "nat", "jft", "jlpt", "qualifications_licenses", "work_experience", "family", "education",
        # "computer_skills", "other_skills", "current_address", "occupation", "nationality"
    )
)

# admin_applicant_list_pydantic = pydantic_model_creator(
#     Applicant, name="Applicant", include=("id", "first_name", "last_name", "email", "phone_number", "img_url", "age", "gender", "birth_place", "marital_status", "recruiter", "organization", "visa", "interview_date",  "created_at")
# )
