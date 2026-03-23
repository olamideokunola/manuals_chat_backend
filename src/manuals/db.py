import os
from dotenv import load_dotenv, dotenv_values

from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import Annotated
from pydantic import ( PostgresDsn )
from pwdlib import PasswordHash

from .models import EquipmentManualChatBot, Organisation, User, Role

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

password_hash = PasswordHash.recommended()

TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD")

def create_seed_data():
    # Get session
    with Session(engine) as session:
        # Create Organisation
        org_name = "Test Organisation"
        existing_org = session.exec(select(Organisation).where(Organisation.name == org_name)).first()
        organisation = None
        if not existing_org:
            organisation = Organisation(
                name=org_name,
                domain="testorganisation.co.uk",
                address="7, Organisation Drive",
                country="United Kingdom"
            )
            session.add(organisation)
            session.commit()

        # Create Roles
        admin_role_name = "admin"
        existing_role = session.exec(select(Role).where(Role.name == admin_role_name)).first()
        if not existing_role:
            admin_role = Role(
                name=admin_role_name
            )
            session.add(admin_role)

        guest_role_name = "guest"
        existing_role = session.exec(select(Role).where(Role.name == guest_role_name)).first()
        if not existing_role:
            guest_role = Role(
                name=guest_role_name
            )
            session.add(guest_role)

        user_role_name = "user"
        existing_role = session.exec(select(Role).where(Role.name == user_role_name)).first()
        if not existing_role:
            user_role = Role(
                name=user_role_name
            )
            session.add(user_role)


        # Create Admin User
        test_user_name = "admin.user@mail.com"
        existing_org = session.exec(select(Organisation).where(Organisation.name == org_name)).first()
        existing_test_user_name = session.exec(select(User).where(User.username == test_user_name)).first()
        existing_admin_role = session.exec(select(Role).where(Role.name == admin_role_name)).first()
        if existing_org and not existing_test_user_name:
            test_user = User(
                username=test_user_name,
                email=test_user_name,
                first_name="Admin",
                last_name="User",
                organisation_id=existing_org.id,
                hashed_password=password_hash.hash(TEST_USER_PASSWORD),
                role=existing_admin_role
            )

            session.add(test_user)
        
        session.commit()
        # session.refresh(test_user)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    create_seed_data()

