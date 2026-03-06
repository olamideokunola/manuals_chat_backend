
from fastapi import UploadFile
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

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
    owner: str | None = None
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