from datetime import date
from typing import Union, Dict, Any, List, Optional
from pydantic import BaseModel, root_validator, validator, EmailStr, SecretStr
from fastapi import UploadFile, File
import json


# class ApplicantSchema(BaseModel):
#     applicant_json: Union[Dict[str, Any], str]
#     display_photo: UploadFile = File(...)
#     licenses: List[UploadFile] = []
#     # licenses: Optional[List[UploadFile]] = None,
#     photos: List[UploadFile] = []

#     @validator('applicant_json', pre=True)
#     def parse_applicant_json(cls, v):
#         if isinstance(v, str):
#             try:
#                 return json.loads(v)
#             except json.JSONDecodeError:
#                 raise ValueError('Invalid JSON format in applicant_json.')
#         elif not isinstance(v, dict):
#             raise ValueError('applicant_json must be either a str or dict.')
#         return v

#     @validator('photos')
#     def validate_image_files(cls, v):
#         """
#         Validate that each file in the photos list is an image.
#         """
#         for file in v:
#             if not file.content_type.startswith('image/'):
#                 raise ValueError('All files in photos must be images.')
#         return v

class UpdateApplicantSchema(BaseModel):
    applicant_json: Union[Dict[str, Any], str]
    display_photo: Optional[UploadFile] = None
    licenses: List[Union[UploadFile, str]] = []
    # photos: List[Optional[UploadFile]] = []

    @validator('applicant_json', pre=True)
    def parse_applicant_json(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('Invalid JSON format in applicant_json.')
        elif not isinstance(v, dict):
            raise ValueError('applicant_json must be either a str or dict.')
        return v

    # @validator('photos', each_item=True)
    # def validate_media_files(cls, v):
    #     """
    #     Validate that each file in the photos list is an image or video.
    #     """
    #     allowed_types = ['image/jpeg', 'image/png',
    #                      'video/mp4', 'video/quicktime', 'video/x-msvideo']
    #     if not any(v.content_type == mime for mime in allowed_types):
    #         raise ValueError('All files must be either images or videos.')
    #     return v

    # @validator('licenses', each_item=True)
    # def validate_licenses(cls, v):
    #     """
    #     Validate that each item in the licenses list is either a valid UploadFile or a URL.
    #     """
    #     # if isinstance(v, str):
    #     # Here you might want to validate that the string is a valid URL.
    #     # if not (v.startswith("http://") or v.startswith("https://")):
    #     #     raise ValueError("URLs must start with http:// or https://")
    #     # return v
    #     if isinstance(v, UploadFile):
    #         # Optional: validate the type of the uploaded file
    #         allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
    #         if v.content_type not in allowed_types:
    #             raise ValueError('Invalid file type for license.')
    #         return v
    #     # else:
    #     #     raise TypeError("Licenses must be either a URL or an UploadFile")


class ApplicantSchema(BaseModel):
    applicant_json: Union[Dict[str, Any], str]
    # display_photo: UploadFile = File(None)
    # licenses: List[UploadFile] = []
    # photos: List[UploadFile] = []
    display_photo: Optional[UploadFile] = None
    licenses: List[Optional[UploadFile]] = []
    photos: List[Optional[UploadFile]] = []

    @validator('applicant_json', pre=True)
    def parse_applicant_json(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('Invalid JSON format in applicant_json.')
        elif not isinstance(v, dict):
            raise ValueError('applicant_json must be either a str or dict.')
        return v

    @validator('photos', each_item=True)
    def validate_media_files(cls, v):
        """
        Validate that each file in the photos list is an image or video.
        """
        allowed_types = ['image/jpeg', 'image/png',
                         'video/mp4', 'video/quicktime', 'video/x-msvideo']
        if not any(v.content_type == mime for mime in allowed_types):
            raise ValueError('All files must be either images or videos.')
        return v


class CreateApplicantToken(BaseModel):
    email: str
    password: str

    @root_validator(pre=True)
    def applicant_validator(cls, values):
        for value in values:
            if len(values.get(value)) == 0:
                raise ValueError('Form has an empty field.')

        return values
