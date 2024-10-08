from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator


class Company(Model):
    id = fields.UUIDField(pk=True, index=True)
    name_en = fields.CharField(max_length=255, null=True)
    name_ja = fields.CharField(max_length=255, null=True)
    prefecture_en = fields.CharField(max_length=255, null=True)
    prefecture_ja = fields.CharField(max_length=255, null=True)
    municipality_town_en = fields.CharField(max_length=255, null=True)
    municipality_town_ja = fields.CharField(max_length=255, null=True)
    street_address_ja = fields.CharField(max_length=255, null=True)
    building_en = fields.CharField(max_length=255, null=True)
    building_ja = fields.CharField(max_length=255, null=True)
    postal_code = fields.CharField(max_length=20, null=True)
    phone = fields.CharField(max_length=20, null=True)
    email = fields.CharField(max_length=255, null=True)
    website = fields.CharField(max_length=255, null=True)
    rep_name_en = fields.CharField(max_length=255, null=True)
    rep_name_ja = fields.CharField(max_length=255, null=True)
    rep_name_ja_kana = fields.CharField(max_length=255, null=True)
    rep_position_en = fields.CharField(max_length=255, null=True)
    rep_position_ja = fields.CharField(max_length=255, null=True)
    rep_phone = fields.CharField(max_length=20, null=True)
    rep_email = fields.CharField(max_length=255, null=True)
    secondary_rep_name_en = fields.CharField(max_length=255, null=True)
    secondary_rep_name_ja = fields.CharField(max_length=255, null=True)
    secondary_rep_name_ja_kana = fields.CharField(max_length=255, null=True)
    secondary_rep_position_en = fields.CharField(max_length=255, null=True)
    secondary_rep_position_ja = fields.CharField(max_length=255, null=True)
    secondary_rep_phone = fields.CharField(max_length=20, null=True)
    secondary_rep_email = fields.CharField(max_length=255, null=True)
    address_ja_reading = fields.TextField(null=True)
    year_established = fields.CharField(max_length=255, null=True)
    registered_industry_ja = fields.CharField(max_length=255, null=True)
    registered_industry_en = fields.CharField(max_length=255, null=True)
    regular_worker_count = fields.IntField(null=True)
    parttime_worker_count = fields.IntField(null=True)
    foreigner_worker_count = fields.IntField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "companies"


company_pydantic = pydantic_model_creator(Company, name="Company")
company_pydantic_in = pydantic_model_creator(
    Company, name="CompanyIn", exclude_readonly=True)

# exclude all except id name en and ja, phone, email, website and created at
company_selection_pydantic = pydantic_model_creator(Company, name="CompanySelect", exclude=('phone', 'email', 'website', 'prefecture_ja', 'municipality_town_ja', 'street_address_ja', 'building_ja', 'postal_code', 'rep_name_en', 'rep_name_ja', 'rep_name_ja_kana',
                                                    'rep_position_en', 'rep_position_ja', 'rep_phone', 'rep_email', 'secondary_rep_name_en', 'secondary_rep_name_ja', 'secondary_rep_name_ja_kana', 'secondary_rep_position_en', 'secondary_rep_position_ja', 'secondary_rep_phone', 'secondary_rep_email', 'address_ja_reading'))
