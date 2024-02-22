import os
import re
import ast

import requests
import torch
from dotenv import load_dotenv

from pathlib import Path


def collate_ix_name(name, version):
    if version:
        return "-".join([name, version])
    return name


# App metadata
# TODO load metadata from pyproject.toml using tomlib instead of this
APP_NAME = "albert-api"
APP_DESCRIPTION = "Albert, also known as LIA: the **L**egal **I**nformation **A**ssistant, is a conversational agent that uses official French data sources to answer administrative agent questions."
APP_VERSION = "2.0.0"
CONTACT = {
    "name": "Etalab - Datalab",
    "url": "https://www.etalab.gouv.fr/",
    "email": "etalab@mail.numerique.gouv.fr",
}

# Root directory:
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Environment:
load_dotenv(os.path.join(ROOT_DIR, ".env"))

ENV = os.getenv("ENV", "dev")
if ENV not in ("unittest", "dev", "prod"):
    raise EnvironmentError("Wrong ENV value")

# CORS
BACKEND_CORS_ORIGINS = [
    "http://localhost:4173",
    "http://localhost:8080",
    "http://ia.etalab.gouv.fr",
    "http://albert.etalab.gouv.fr",
    "http://albert.staging.etalab.gouv.fr",
    "http://franceservices.etalab.gouv.fr",
    "http://franceservices.staging.etalab.gouv.fr",
    "https://ia.etalab.gouv.fr",
    "https://albert.etalab.gouv.fr",
    "https://albert.staging.etalab.gouv.fr",
    "https://franceservices.etalab.gouv.fr",
    "https://franceservices.staging.etalab.gouv.fr",
]

# JWT token
SECRET_KEY = os.environ["SECRET_KEY"]
PASSWORD_PATTERN = r"^[A-Za-z\d$!%*+\-?&#_=.,:;@]{8,128}$"

# Database
FIRST_ADMIN_USERNAME = os.environ["FIRST_ADMIN_USERNAME"]
FIRST_ADMIN_EMAIL = os.environ["FIRST_ADMIN_EMAIL"]
FIRST_ADMIN_PASSWORD = os.environ["FIRST_ADMIN_PASSWORD"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

# Email
MJ_API_KEY = os.getenv("MJ_API_KEY")
MJ_API_SECRET = os.getenv("MJ_API_SECRET")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL")

# Public Urls
API_URL = os.getenv("API_URL", "https://albert.etalab.gouv.fr")
FRONT_URL = os.getenv("FRONT_URL", "https://albert.etalab.gouv.fr")
API_ROUTE_VER = "/api/v2"
# For local testing, use:
# --
# API_URL = "http://localhost:8000"
# API_ROUTE_VER = "/"

# Search Engines
ELASTICSEARCH_URL = "http://127.0.0.1:9202"
ELASTICSEARCH_CREDS = ("elastic", "changeme")
QDRANT_URL = "http://127.0.0.1:6333"
ELASTICSEARCH_IX_VER = "v3"
QDRANT_IX_VER = "v3"
SHEET_SOURCES = ["service-public", "travail-emploi"]
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
EMBEDDING_BOOTSTRAP_PATH = os.path.join(
    "_data", "embeddings", EMBEDDING_MODEL.split("/")[-1]
)

# LLM Routing Table.
LLM_TABLE = os.getenv("LLM_TABLE")
if not LLM_TABLE:  # default
    LLM_TABLE = [
        # model_name/api URL
        ("albert-light", "http://127.0.0.1:8082")
    ]
else:
    try:
        LLM_TABLE = ast.literal_eval(LLM_TABLE)
    except Exception as e:
        raise ValueError("LLM_TABLE is not valid: %s" % e)


PASSWORD_RESET_TOKEN_TTL = 3600  # seconds
ACCESS_TOKEN_TTL = 3600 * 24  # seconds
if ENV == "unittest":
    PASSWORD_RESET_TOKEN_TTL = 3  # seconds
    ACCESS_TOKEN_TTL = 9  # seconds

# If local, download the model Tiny Albert from HuggingFace
if ENV == "dev":
    TINY_ALBERT_LOCAL_PATH = Path("tiny_albert.bin").resolve()
    if not TINY_ALBERT_LOCAL_PATH.exists():
        print(
            "Downloading Tiny Albert model for local usage since it's not present locally already. It's 7.3GB so it might take a few dozen minutes..."
        )
        response = requests.get(
            "https://huggingface.co/ActeurPublic/tiny-albert/resolve/main/ggml-model-expert-q4_K.bin",
            stream=True,
        )
        open(str(TINY_ALBERT_LOCAL_PATH), "wb").write(response.content)
        print("Done!")

if torch.cuda.is_available():
    WITH_GPU = True
    DEVICE_MAP = "cuda:0"
else:
    WITH_GPU = False
    DEVICE_MAP = None
