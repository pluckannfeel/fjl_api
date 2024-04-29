from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator


class Organization(Model):
    id = fields.UUIDField(pk=True, index=True)
    org_name = fields.CharField(max_length=255, null=False)
    org_type = fields.CharField(max_length=255, null=False)
    org_date_established = fields.DateField(null=False)
    org_address = fields.TextField(null=False)
    org_contact = fields.CharField(max_length=255, null=False)
    org_email = fields.CharField(max_length=255, null=False)
    org_website = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

org_pydantic = pydantic_model_creator(
    Organization, name="Organization", 
)