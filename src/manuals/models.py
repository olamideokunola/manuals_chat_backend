
from fastapi import UploadFile
from pydantic import BaseModel
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select



# AUTH Models
class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    username: str | None = None



# Organisation
class Organisation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    domain: str
    address: str
    country: str

    users: list['User'] = Relationship(back_populates="organisation")
    groups: list['Group'] = Relationship(back_populates="organisation")
    chat_bots: list['EquipmentManualChatBot'] = Relationship(back_populates="organisation")

# Role
class Role(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)

    users: list['User'] = Relationship(back_populates="role")

# User Models
class UserBase(SQLModel):
    username: str
    email: str | None = None
    first_name: str
    last_name: str
    disabled: bool | None = None

class EquipmentManualChatbotUser(SQLModel, table=True):
    chatbot_id: int = Field(foreign_key="equipmentmanualchatbot.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)

# class UserRole(SQLModel, table=True):
#     user_id: int = Field(foreign_key="user.id", primary_key=True)
#     role_id: int = Field(foreign_key="role.id", primary_key=True)

class UserGroup(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    group_id: int = Field(foreign_key="group.id", primary_key=True)

class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str

    organisation_id: int = Field(foreign_key="organisation.id")
    organisation: Organisation = Relationship(back_populates="users")

    created_chat_bots: list["EquipmentManualChatBot"] = Relationship(back_populates="creator")
    
    chat_bots: list["EquipmentManualChatBot"] = Relationship(back_populates="users", link_model=EquipmentManualChatbotUser)
    
    role_id: int = Field(foreign_key="role.id")
    role: Role = Relationship(back_populates="users")

    groups: list["Group"] = Relationship(back_populates="users", link_model=UserGroup)

class UserWithId(UserBase):
    id: int

class UserPublic(UserBase):
    id: int
    role: str | None

class UserCreateBase(UserBase):
    username: str
    email: str
    first_name: str
    last_name: str
    disabled: bool | None = None

class UserCreateForm(UserCreateBase):
    password: str




    

class EquipmentManualChatbotGroup(SQLModel, table=True):
    chatbot_id: int = Field(foreign_key="equipmentmanualchatbot.id", primary_key=True)
    group_id: int = Field(foreign_key="group.id", primary_key=True)

# Group   
class Group(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)

    organisation_id: int = Field(foreign_key="organisation.id")
    organisation: Organisation = Relationship(back_populates="groups")

    users: list['User'] = Relationship(back_populates="groups", link_model=UserGroup)

    chat_bots: list['EquipmentManualChatBot'] = Relationship(back_populates="groups", link_model=EquipmentManualChatbotGroup)



# ChatBot
class ChatBotFormModel(BaseModel):
    file: UploadFile
    title: str
    equipment_type: str
    chatbot_purpose: str
    owner: str
    description: str
    collection_name: str
    system_prompt: str

class ChatBotFormModelUpdate(ChatBotFormModel):
    file: UploadFile | None = None
    title: str | None = None
    equipment_type: str | None = None
    chatbot_purpose: str | None = None
    owner: str | None = None
    description: str | None = None
    collection_name: str | None = None
    system_prompt: str | None = None

class EquipmentManualChatBotBase(SQLModel):
    name: str = Field(index=True)
    equipment_type: str
    manual_title: str
    chatbot_purpose: str
    description: str | None = None
    owner: str
    collection_name: str
    system_prompt: str



class EquipmentManualChatBot(EquipmentManualChatBotBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    file_name: str

    organisation_id: int = Field(foreign_key="organisation.id")
    organisation: Organisation = Relationship(back_populates="chat_bots")
    
    creator_id: int = Field(foreign_key="user.id")
    creator: User = Relationship(back_populates="created_chat_bots")

    users: list['User'] = Relationship(back_populates="chat_bots", link_model=EquipmentManualChatbotUser)

    groups: list['Group'] = Relationship(back_populates="chat_bots", link_model=EquipmentManualChatbotGroup)


class EquipmentManualChatBotForm(EquipmentManualChatBotBase):
    file: UploadFile | None = None

class EquipmentManualChatBotCreate(EquipmentManualChatBotBase):
    file_name: str

class EquipmentManualChatBotFormUpdate(EquipmentManualChatBotBase):
    file: UploadFile | None = None
    name: str | None = None
    equipment_type: str | None = None
    manual_title: str | None = None
    chatbot_purpose: str | None = None
    description: str | None = None
    owner: str | None = None #Admin user
    file_name: str | None = None
    collection_name: str | None = None
    system_prompt: str | None = None

class EquipmentManualChatBotUpdate(EquipmentManualChatBotBase):
    name: str | None = None
    equipment_type: str | None = None
    manual_title: str | None = None
    chatbot_purpose: str | None = None
    description: str | None = None
    owner: str | None = None
    file_name: str | None = None
    collection_name: str | None = None
    system_prompt: str | None = None
