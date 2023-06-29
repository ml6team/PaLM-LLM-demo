import os
from dotenv import load_dotenv


load_dotenv()

ES_HOST = os.getenv('ES_HOST')
ES_USER = os.getenv('ES_USER')
ES_PASS = os.getenv('ES_PASS')
GCP_PROJECT = os.getenv('GCP_PROJECT')
