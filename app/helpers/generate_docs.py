import os
import boto3
from dotenv import load_dotenv
from datetime import datetime
from app.helpers.s3_file_upload import generate_s3_url
from tempfile import TemporaryDirectory
from io import BytesIO
from docx import Document
import logging

load_dotenv()

# Initialize S3 client
s3 = boto3.client('s3')

# Define the directory for static files (relative to the current working directory)
STATIC_DIR = "app/static"

contracts_folder = 'uploads/admin/contracts/'
bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")


class JobDetails:
    def __init__(self, id: int, title: str, no_of_workers: int, basic_salary: str):
        self.id = id
        self.title = title
        self.no_of_workers = no_of_workers
        self.basic_salary = basic_salary

# Set up logging
# logging.basicConfig(level=logging.DEBUG)

# Function to replace placeholders in a single paragraph, handling split runs


def replace_text_in_paragraph(paragraph, placeholder, replacement):
    paragraph_text = ''.join(run.text for run in paragraph.runs)
    if placeholder in paragraph_text:
        # logging.debug(f"Replacing placeholder in paragraph: {placeholder} -> {replacement}")
        paragraph_text = paragraph_text.replace(placeholder, str(replacement))

        # Clear the existing runs and re-add the modified text
        for run in paragraph.runs:
            run.text = ''
        paragraph.runs[0].text = paragraph_text

# Function to replace placeholders in the entire document


def replace_placeholder(doc, placeholder, replacement):
    # logging.debug(f"Replacing placeholder: {placeholder} -> {replacement}")
    for paragraph in doc.paragraphs:
        replace_text_in_paragraph(paragraph, placeholder, replacement)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                replace_placeholder(cell, placeholder, replacement)

# Function to fill the template with the replacements


def fill_template(template_path, output_path, replacements):
    doc = Document(template_path)
    for placeholder, replacement in replacements.items():
        replace_placeholder(doc, f"{{{{{placeholder}}}}}", replacement)
    doc.save(output_path)


def fill_application_form(company, agency, details):
    created_at = datetime.now()
    year = created_at.year
    month = created_at.month
    day = created_at.day

    #current date
    today = datetime.now()

    # new_document_name = "application_form_test.docx"
    new_document_name = f"MWO_申込書_{company.name_en}_{today.strftime('%Y%m%d')}.docx"
    original_file = os.path.join(STATIC_DIR, "application_form.docx")
    s3_new_document = f"{contracts_folder}{new_document_name}"

    # replacements = {
    #     "company_name_en": "Make You Smile Co., Ltd.",
    #     "rep_name_en": "Kazuhiro Ito",
    #     "rep_position_en": "President",
    #     "address": "#304 YT Bashamichi Bldg, 4-20-2 Kaigandori, Naka-ku, Yokohama shi, Kanagawa Pref.",
    #     "postal_code": "231-0002",
    #     "phone": "050-5894-1192",
    #     "website": "https://www.makeyousmile.jp/",
    #     "rep_email": "kazuhiro110@makeyousmile.jp",
    #     "agency_name": "AQIUM INTERNATIONAL INC.",
    #     "agency_address": "Unit 2A, 3A & 3B, 4K Plaza Bldg., 677 Shaw Blvd., Brgy. Kapitolyo, Pasig City, Philippines",
    # }

    replacements = {
        "company_name_en": company.name_en,
        "rep_name_en": company.rep_name_en,
        "rep_position_en": company.rep_position_en,
        "address": f"{company.building_en}, {company.municipality_town_en}, {company.prefecture_en}",
        "postal_code": company.postal_code,
        "phone": company.phone,
        "website": company.website,
        "rep_email": company.rep_email,
        "agency_name": agency.name,
        "agency_address": agency.address,
    }

    with TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, new_document_name)

        new_contract_buffer = BytesIO()
        fill_template(original_file, temp_file_path, replacements)

        with open(temp_file_path, 'rb') as temp_file:
            new_contract_buffer.write(temp_file.read())

        s3.upload_file(temp_file_path, Bucket=bucket_name, Key=s3_new_document, ExtraArgs={
            'ACL': 'public-read', 'ContentType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'})

    s3_read_url = generate_s3_url(s3_new_document, 'read')
    return s3_read_url


def fill_manpower_request_template(template_path, output_path, replacements, job_details, total_workers):
    doc = Document(template_path)
    for placeholder, replacement in replacements.items():
        replace_placeholder(doc, f"{{{{{placeholder}}}}}", replacement)

    # Handle the job details insertion
    table = doc.tables[0]
    for detail in job_details:
        row_cells = table.add_row().cells
        row_cells[0].text = detail['title']
        row_cells[1].text = str(detail['no_of_workers'])
        row_cells[2].text = detail['basic_salary']

    # Add the total number of workers row
    total_row_cells = table.add_row().cells
    total_row_cells[0].text = "TOTAL Number of Workers"
    total_row_cells[1].text = str(total_workers)
    total_row_cells[2].text = ""

    doc.save(output_path)


def fill_manpower_request_form(company, agency, details):
    # created_at = datetime.now()
    # year = created_at.year
    # month = created_at.month
    # month_name = created_at.strftime("%b")
    # day = created_at.day

    # retrieve created_date from details and convert to date
    if details['created_date'] is None or details['created_date'] == "":
        created_date = datetime.now()
    else:
        created_date = datetime.strptime(details['created_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        
    year = created_date.year
    month = created_date.month
    month_name = created_date.strftime("%b")
    day = created_date.day

    #current date
    today = datetime.now()

    # new_document_name = "manpower_request_form_test.docx"
    new_document_name = f"MWO_MANPOWER_REQUEST_{company.name_en}_{today.strftime('%Y%m%d')}.docx"
    original_file = os.path.join(STATIC_DIR, "manpower_request.docx")
    s3_new_document = f"{contracts_folder}{new_document_name}"

    # replacements = {
    #     "created_date": f"{day} {month_name}, {year}",
    #     "company_name_en": "Make You Smile Co., Ltd.",
    #     "rep_name_en": "Kazuhiro Ito",
    #     "rep_position_en": "President",
    #     "building": "#304 YT Bashamichi Bldg",
    #     "street": "4-20-2 Kaigandori",
    #     "city": "Naka-ku, Yokohama shi",
    #     "prefecture": "Kanagawa Pref.",
    #     "postal_code": "231-0002",
    #     "phone": "050-5894-1192",
    #     "website": "https://www.makeyousmile.jp/",
    #     "rep_email": "kazuhiro110@makeyousmile.jp",
    #     "agency_name": "AQIUM INTERNATIONAL INC.",
    #     "agency_address": "Unit 2A, 3A & 3B, 4K Plaza Bldg., 677 Shaw Blvd., Brgy. Kapitolyo, Pasig City, Philippines",
    #     "agency_rep_name": "Ms. HERMARANOEMI B. ALBERTO",
    #     "agency_rep_position": "Director",
    #     "visa_type": "Engineer / Specialist in Humanities / International Services",
    # }

    replacements = {
        "created_date": f"{day} {month_name}, {year}",
        "company_name_en": company.name_en,
        "rep_name_en": company.rep_name_en,
        "rep_position_en": company.rep_position_en,
        "building": company.building_en,
        # "street": "4-20-2 Kaigandori",
        "street": "",
        "city": company.municipality_town_en,
        "prefecture": company.prefecture_en,
        "postal_code": company.postal_code,
        "phone": company.phone,
        "website": company.website,
        "rep_email": company.rep_email,
        "agency_name": agency.name,
        "agency_address": agency.address,
        "agency_rep_name": agency.rep_name,
        "agency_rep_position": agency.rep_position,
        "visa_type": details['visa_type'],
    }

    job_details = details['job_details']
    # total_workers = sum(detail['no_of_workers'] for detail in job_details)
    total_workers = details['total_workers']

    with TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, new_document_name)

        new_contract_buffer = BytesIO()
        fill_manpower_request_template(
            original_file, temp_file_path, replacements, job_details, total_workers)

        with open(temp_file_path, 'rb') as temp_file:
            new_contract_buffer.write(temp_file.read())

        s3.upload_file(temp_file_path, Bucket=bucket_name, Key=s3_new_document, ExtraArgs={
            'ACL': 'public-read', 'ContentType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'})

    s3_read_url = generate_s3_url(s3_new_document, 'read')
    return s3_read_url


def fill_employment_contract(company, agency, details):
    # created_at = datetime.now()
    # year = created_at.year
    # month = created_at.month
    # day = created_at.day

    if details['created_date'] is None or details['created_date'] == "":
        created_date = datetime.now()
    else:
        created_date = datetime.strptime(details['created_date'], "%Y-%m-%dT%H:%M:%S.%fZ")

    year = created_date.year
    month = created_date.month
    month_name = created_date.strftime("%b")
    day = created_date.day

    #current date
    today = datetime.now()

    # new_document_name = "employment_contract_test.docx"
    new_document_name = f"MWO_EMPLOYMENT_CONTRACT_{company.name_en}_{today.strftime('%Y%m%d')}.docx"
    original_file = os.path.join(STATIC_DIR, "employment_contract.docx")
    s3_new_document = f"{contracts_folder}{new_document_name}"

    # replacements = {
    #     "created_date": f"{day} {month}, {year}",
    #     "company_name_en": "Make You Smile Co., Ltd.",
    #     "company_address": "#304 YT Bashamichi Bldg, 4-20-2 Kaigandori, Naka-ku, Yokohama shi, Kanagawa Pref.",
    #     "company_rep_name_en": "Kazuhiro Ito",
    #     "company_rep_position_en": "President",
    #     "building": "#304 YT Bashamichi Bldg",
    #     "street": "4-20-2 Kaigandori",
    #     "city": "Naka-ku, Yokohama shi",
    #     "prefecture": "Kanagawa Pref.",
    #     "postal_code": "231-0002",
    #     "company_phone": "050-5894-1192",
    #     "website": "https://www.makeyousmile.jp/",
    #     "rep_email": "kazuhiro110makeyousmile.jp",
    #     "agency_name": "AQIUM INTERNATIONAL INC.",
    #     "agency_address": "Unit 2A, 3A & 3B, 4K Plaza Bldg., 677 Shaw Blvd., Brgy. Kapitolyo, Pasig City, Philippines",
    #     "agency_rep_name": "Ms. HERMARANOEMI B. ALBERTO",
    #     "agency_rep_position": "Director",
    #     "employment_address": "Japan",
    #     "employment_term": "3 years",
    #     "job_position_title": "Software Engineer",
    #     "job_position_description": "Develop software applications",
    # }


    if details['passport_date_issued'] is None or details['passport_date_issued'] == "":
        pdi_year = ""
        pdi_month = ""
        pdi_month_name = ""
        pdi_day = ""
    else :
        passport_date_issued = datetime.strptime(
        details['passport_date_issued'], "%Y-%m-%dT%H:%M:%S.%fZ")
    
        pdi_year = passport_date_issued.year
        pdi_month = passport_date_issued.month
        pdi_month_name = passport_date_issued.strftime("%b")
        pdi_day = passport_date_issued.day

    replacements = {
        "created_date": f"{day} {month_name}, {year}",
        "company_name_en": company.name_en,
        "company_address": f"{company.building_en}, {company.municipality_town_en}, {company.prefecture_en}",
        "company_rep_name_en": company.rep_name_en,
        "company_rep_position_en": company.rep_position_en,
        "building": company.building_en,
        "street": "",
        "city": company.municipality_town_en,
        "prefecture": company.prefecture_en,
        "postal_code": company.postal_code,
        "company_phone": company.phone,
        "website": company.website,
        "rep_email": company.rep_email,
        "agency_name": agency.name,
        "agency_address": agency.address,
        "agency_rep_name": agency.rep_name,
        "agency_rep_position": agency.rep_position,
        "worker_name": details['worker_name'],
        "philippine_address": details['philippine_address'],
        "civil_status": details['civil_status'],
        "passport_no": details['passport_no'],
        "passport_date_issued": f"{pdi_month_name} {pdi_day}, {pdi_year}",
        "passport_place_issued": details['passport_place_issued'],
        "employment_address": details['employment_address'],
        "employment_term": details['employment_term'],
        "job_position_title": details['job_position_title'],
        "job_position_description": details['job_position_description'],
    }

    with TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, new_document_name)

        new_contract_buffer = BytesIO()
        fill_template(original_file, temp_file_path, replacements)

        with open(temp_file_path, 'rb') as temp_file:
            new_contract_buffer.write(temp_file.read())

        s3.upload_file(temp_file_path, Bucket=bucket_name, Key=s3_new_document, ExtraArgs={
            'ACL': 'public-read', 'ContentType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'})

    s3_read_url = generate_s3_url(s3_new_document, 'read')
    return s3_read_url


def fill_recruitment_agreement(company, agency, details):
    if details['created_date'] is None or details['created_date'] == "":
        created_date = datetime.now()
    else:
        created_date = datetime.strptime(details['created_date'], "%Y-%m-%dT%H:%M:%S.%fZ")

    year = created_date.year
    month = created_date.month
    month_name = created_date.strftime("%B")
    day = created_date.day

    #current date
    today = datetime.now()

    # new_document_name = f"MWO_雇用契約書_{company.name_en}_{created_date.strftime('%Y%m%d')}.docx"
    new_document_name = f"MWO_RECRUITMENTAGREEMENT_{company.name_en}_{today.strftime('%Y%m%d')}.docx"
    original_file = os.path.join(STATIC_DIR, "recruitment_agreement.docx")
    s3_new_document = f"{contracts_folder}{new_document_name}"

    replacements = {
        "created_date": f"{day} {month_name}, {year}",
        "year": year,
        "month": month,
        "month_name": month_name,
        "day": day,
        "company_name_en": company.name_en,
        "company_address_en": f"{company.building_en}, {company.municipality_town_en}, {company.prefecture_en}",
        "company_rep_name_en": company.rep_name_en,
        "company_rep_position_en": company.rep_position_en,
        "company_name_ja": company.name_ja,
        "company_address_ja": f"{company.prefecture_ja}, {company.municipality_town_ja} {company.street_address_ja}, {company.building_ja}",
        "company_rep_name_ja": company.rep_name_ja,
        "company_rep_position_ja": company.rep_position_ja,
        "postal_code": company.postal_code,
        "rep_email": company.rep_email,
        "agency_name": agency.name,
        "agency_address": agency.address,
        "agency_rep_name": agency.rep_name,
        "agency_rep_position": agency.rep_position,
    }

    with TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, new_document_name)

        new_contract_buffer = BytesIO()
        fill_template(original_file, temp_file_path, replacements)

        with open(temp_file_path, 'rb') as temp_file:
            new_contract_buffer.write(temp_file.read())

        s3.upload_file(temp_file_path, Bucket=bucket_name, Key=s3_new_document, ExtraArgs={
            'ACL': 'public-read', 'ContentType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'})
        
    s3_read_url = generate_s3_url(s3_new_document, 'read')
    return s3_read_url

def generate_default_documents(document_name: str):
    if document_name == 'aqium_license_copy':
        # retrieve the aqium_license_copy.pdf file, upload to s3 and return the s3 url
        new_document_name = "★AQIUMライセンスの写し.pdf"
        original_file = os.path.join(STATIC_DIR, "aqium_license_copy.pdf")

        s3_new_document = f"{contracts_folder}{new_document_name}"

        with open(original_file, 'rb') as file:
            s3.upload_fileobj(file, bucket_name, s3_new_document, ExtraArgs={
                'ACL': 'public-read', 'ContentType': 'application/pdf'})
            
        s3_read_url = generate_s3_url(s3_new_document, 'read')

        return s3_read_url
    elif document_name == 'aqium_representative_passport_copy':
        # retrieve the aqium_representative_passport_copy.pdf file, upload to s3 and return the s3 url
        new_document_name = "★AQIUM代表者のパスポートの写し.pdf"
        original_file = os.path.join(STATIC_DIR, "noemi_passport_copy.pdf")

        s3_new_document = f"{contracts_folder}{new_document_name}"

        with open(original_file, 'rb') as file:
            s3.upload_fileobj(file, bucket_name, s3_new_document, ExtraArgs={
                'ACL': 'public-read', 'ContentType': 'application/pdf'})
            
        s3_read_url = generate_s3_url(s3_new_document, 'read')

        return s3_read_url