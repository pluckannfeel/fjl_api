import os
import boto3
import shutil
import time
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError
from app.helpers.definitions import get_directory_path
from tempfile import NamedTemporaryFile
from fastapi import UploadFile
import datetime

load_dotenv()

access_key = os.environ["AWS_ACCESS_KEYID"]
secret_access_key = os.environ["AWS_SECRET_ACCESSKEY"]

client = boto3.client('s3',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_access_key)

# file upload
upload_path = get_directory_path() + '\\uploads'

bucket_name = os.environ["AWS_STORAGE_BUCKET_NAME"]

# def upload_file_to_s3(file_object, app_type):
#     if app_type == 'professional':
#         object_name = 'uploads/pdf/professional/' + file_object.filename
#     elif app_type == 'ssw':
#         object_name = 'uploads/pdf/ssw/' + file_object.filename
#     elif app_type == 'trainee':
#         object_name = 'uploads/pdf/trainee/' + file_object.filename

#     temp = NamedTemporaryFile(delete=False)
#     try:
#         try:
#             contents = file_object.file.read()
#             with temp as f:
#                 f.write(contents)
#         except ClientError as e:
#             return {"message": "There was an error uploading the file. " + str(e)}
#         finally:
#             file_object.file.close()

#         # upload here
#         client.upload_file(temp.name, bucket_name, object_name, ExtraArgs={"ACL": 'public-read', "ContentType": file_object.content_type})

#     except ClientError as e:
#         return {"message": "There was an error processing the file.", "error": e}
#     finally:
#         os.remove(temp.name)
#         # print(contents)  # Handle file contents as desired
#         return {"filename": file_object.filename}


def upload_image_to_s3(imageFile, new_image_name, folder_path):
    object_name = f'{folder_path}/{new_image_name}'
    temp = NamedTemporaryFile(delete=False)
    try:
        try:
            contents = imageFile.file.read()
            with temp as f:
                f.write(contents)
        except ClientError as e:
            return {"message": "There was an error uploading the file. " + str(e)}
        finally:
            imageFile.file.close()

        client.upload_file(temp.name, bucket_name, object_name, ExtraArgs={
                           "ACL": 'public-read', "ContentType": imageFile.content_type})

        return new_image_name

        # # upload here
        # client.upload_file(temp.name, bucket_name, object_name, ExtraArgs={"ACL": 'public-read', "ContentType": imageFile.content_type})

        # #  rename s3 uploaded file
        # client.copy_object(Bucket=bucket_name, CopySource=bucket_name + '/' + object_name, Key='uploads/img/' + new_image_name, ACL='public-read')

        # # delete old file
        # response = client.delete_object(
        #     Bucket=bucket_name,
        #     Key=object_name,
        #     )
        # print('delete', response)
    except ClientError as e:
        return {"message": "There was an error processing the file.", "error": e}
    finally:
        os.remove(temp.name)
        # print(contents)  # Handle file contents as desired
        return {"filename": imageFile.filename}


# def upload_file_to_s3(file_object: UploadFile, new_file_name: str, folder_path: str):
#     # Construct the full S3 object name
#     object_name = f'{folder_path}{new_file_name}'
#     temp_file = NamedTemporaryFile(delete=False)
#     try:
#         # Read the contents from UploadFile to a temporary file
#         contents = file_object.file.read()
#         with open(temp_file.name, 'wb') as f:
#             f.write(contents)  # Write the contents to a temporary file

#         # Upload the temporary file to S3
#         client.upload_file(Filename=temp_file.name, Bucket='your-bucket-name', Key=object_name, ExtraArgs={
#                            "ACL": 'public-read', "ContentType": file_object.content_type})
#         # Returning the new_file_name for use in the API response
#         return {"filename": new_file_name}
#     except ClientError as e:
#         return {"message": "There was an error uploading the file to S3.", "error": str(e)}
#     finally:
#         file_object.file.close()  # Close the file to clean up the file handle
#         # Remove the temporary file to clean up disk space
#         os.remove(temp_file.name)

def upload_file_to_s3(file_object, new_file_name, folder_path):
    # slash is not needed
    object_name = f'{folder_path}{new_file_name}'
    temp = NamedTemporaryFile(delete=False)
    try:
        try:
            contents = file_object.file.read()
            with temp as f:
                f.write(contents)

            print("Successfully read file contents")
        except ClientError as e:
            print("Inner Upload file to S3 error: ", e)
            return {"message": "There was an error uploading the file. " + str(e)}
        finally:
            file_object.file.close()

        # upload here
        client.upload_file(temp.name, bucket_name, object_name, ExtraArgs={
                           "ACL": 'public-read', "ContentType": file_object.content_type})

        print("Successfully uploaded file to s3")

        return new_file_name
    except ClientError as e:
        print("Outer Upload file to S3 error: ", e)
        return {"message": "There was an error processing the file.", "error": e}
    finally:
        os.remove(temp.name)
        # print(contents)  # Handle file contents as desired
        return {"filename": file_object.filename}


# generate s3 bucket url
def generate_s3_url(file_name, access_type):
    # print(f"file_name :{file_name}")
    try:
        # expiration_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=)

        if access_type == 'read':
            url = client.generate_presigned_url(
                'get_object', Params={'Bucket': bucket_name, 'Key': file_name}, ExpiresIn=60)

            # cut off the query string
            url = url.split('?')[0]
        elif access_type == 'write':
            url = client.generate_presigned_url(
                'put_object', Params={'Bucket': bucket_name, 'Key': file_name}, ExpiresIn=60)

        # print("url: ", url)

        return url
    except NoCredentialsError:
        print("Credentials not available")


def is_file_exists(file_path):
    try:
        response = client.head_object(Bucket=bucket_name, Key=file_path)
        # print(response)
        return True
    except ClientError as e:
        return False
