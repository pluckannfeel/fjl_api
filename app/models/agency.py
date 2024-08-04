from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator


class Agency(Model):
    id = fields.UUIDField(pk=True, index=True)
    

agency_pydantic = pydantic_model_creator(
    Agency, name="Agency", 
)