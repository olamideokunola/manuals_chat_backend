import os
from dotenv import load_dotenv, dotenv_values

from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import Annotated
from pydantic import ( PostgresDsn )

from .models import EquipmentManualChatBot

load_dotenv()

POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER")
POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT"))
POSTGRES_USER: str = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB: str = os.getenv("POSTGRES_DB")

def SQLALCHEMY_DATABASE_URI() -> PostgresDsn:
    return PostgresDsn.build(
        scheme="postgresql+psycopg",
        username=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_SERVER,
        port=POSTGRES_PORT,
        path=POSTGRES_DB,
    )

engine = create_engine(str(SQLALCHEMY_DATABASE_URI()))

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

