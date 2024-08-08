from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator


class Agency(Model):
    id = fields.UUIDField(pk=True, index=True)
    name = fields.CharField(max_length=255, null=True)
    address = fields.TextField(null=True)
    phone = fields.CharField(max_length=20, null=True)
    email = fields.CharField(max_length=255, null=True)
    website = fields.CharField(max_length=255, null=True)
    rep_name = fields.CharField(max_length=255, null=True)
    rep_position = fields.CharField(max_length=255, null=True)
    rep_phone = fields.CharField(max_length=20, null=True)
    rep_email = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    

agency_pydantic = pydantic_model_creator(
    Agency, name="Agency", 
)

agency_selection_pydantic = pydantic_model_creator(
    Agency, name="AgencySelect", exclude=('address', 'phone', 'email', 'website', 'rep_name', 'rep_position', 'rep_phone', 'rep_email')
)