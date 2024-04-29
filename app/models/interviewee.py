from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator


class Interviewee(Model):
    id = fields.UUIDField(pk=True, index=True)
    img_url = fields.TextField(null=True)
    first_name = fields.CharField(max_length=128, null=False)
    last_name = fields.CharField(max_length=128, null=False)
    middle_name = fields.CharField(max_length=128, null=True)
    birth_date = fields.DateField(null=True)
    age = fields.IntField(null=True)
    gender = fields.CharField(max_length=10, null=True)
    nationality = fields.CharField(max_length=128, null=True)
    university_name = fields.CharField(max_length=256, null=True)
    # selected_dates = fields.TextField(null=True)
    selected_dates = fields.JSONField(null=True)
    residence_card_number = fields.CharField(
        max_length=128, null=True)
    residence_card_expiry = fields.DateField(null=True)
    residence_card_image = fields.TextField(null=True)
    phone_number = fields.CharField(max_length=128, null=True)
    email = fields.CharField(max_length=200, null=False, )
    password_hash = fields.CharField(max_length=128, null=True)
    is_verified = fields.BooleanField(default=False, null=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    @staticmethod
    def get_full_name(self) -> str:
        return self.first_name + ' ' + self.last_name

    def __str__(self):
        return self.first_name + ' ' + self.last_name

    class Meta:
        table = "interviewees"
        ordering = ["-created_at"]


interviewee_pydantic = pydantic_model_creator(Interviewee, name="Interviewee")
