import os

from fastapi import Depends, Form, HTTPException
from sqlmodel import Session, select
from typing import Annotated

from .src.manuals.db import engine
from .src.manuals.models import EquipmentManualChatBot, EquipmentManualChatBotFormUpdate, EquipmentManualChatBotUpdate, EquipmentManualChatBotForm
from .src.manuals.embeddings import AgentWrapper, EquipmentManualContextManager


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

def get_chatbot_config(chat_id: int, session: SessionDep):
    chatbot_config = session.get(EquipmentManualChatBot, chat_id)
    return chatbot_config

async def form_data(data: Annotated[EquipmentManualChatBotForm | None, Form()]=None):
    print('in form_data, data is {}'.format(data))
    return data

class FileUploader:
    def __init__(self, data: Annotated[EquipmentManualChatBotForm | EquipmentManualChatBotFormUpdate, Form()]):
        if data.file != None:
            self.data = data
            self.file_extension = data.file.filename.split('.')[-1]
            self.file_name = f"{data.manual_title}.{self.file_extension}"
            folder_path = "data/manual_uploads/{}".format(self.data.owner)
            
            os.makedirs(folder_path, exist_ok=True)        
            self.full_path = os.path.join(folder_path, self.file_name)

    async def uploadfile(self):
        with open(self.full_path, "wb") as f:
            await self.data.file.seek(0)
            contents = await self.data.file.read()
            f.write(contents)


class DataStoreManager:
    def __init__(
        self,
        session: SessionDep
    ):
        self.session = session

    def get_chatbot_config_with_title(self, title: str) -> EquipmentManualChatBot:
        find_title_stmt = select(EquipmentManualChatBot).where(EquipmentManualChatBot.manual_title == title)
        results = self.session.exec(find_title_stmt)
        chatbot_config = results.first()
        return chatbot_config

    def get_chatbot_config(self, chat_id: int):
        if chat_id == None:
            raise HTTPException(status_code=404, detail="config not found")
        chatbot_config = self.session.get(EquipmentManualChatBot, chat_id)
        return chatbot_config
    
    def save_chat_config(self, data: EquipmentManualChatBot, file_name: str):
        file_extension = data.file.filename.split('.')[-1]
        manualChatBot = EquipmentManualChatBot(
            name=data.name,
            manual_title=data.manual_title,
            equipment_type=data.equipment_type,
            chatbot_purpose=data.chatbot_purpose,
            description=data.description,
            owner=data.owner,
            file_name=file_name,
            collection_name=data.collection_name,
            system_prompt=data.system_prompt
        )
        
        self.session.add(manualChatBot)
        self.session.commit()
        self.session.refresh(manualChatBot)

        return manualChatBot

    def get_chabot_configs_for_owner(self, owner: str) -> list[EquipmentManualChatBot]:
        owner_chatbots_stmt = select(EquipmentManualChatBot).where(EquipmentManualChatBot.owner == owner)
        results = self.session.exec(owner_chatbots_stmt)
        return results

    def update_chat_config(self, chat_id:int, data: EquipmentManualChatBotFormUpdate, file_name:str | None=None):
        chatbot_config = self.get_chatbot_config(chat_id)

        if not chatbot_config:
            raise HTTPException(status_code=404, detail="chatbot config not found")

        chatbot_config_update = EquipmentManualChatBotUpdate(
            name=data.name,
            manual_title=data.manual_title,
            equipment_type=data.equipment_type,
            chatbot_purpose=data.chatbot_purpose,
            description=data.description,
            owner=data.owner,
            file_name=file_name,
            collection_name=data.collection_name,
            system_prompt=data.system_prompt
        )

        if data.name:
            chatbot_config.name = data.name
        
        if data.name:
            chatbot_config.name = data.name

        set_keys = [name for name in chatbot_config_update.__dict__.keys() if chatbot_config_update.__dict__[name] != None]

        chatbot_config_data = {}
        for key in set_keys:
            chatbot_config_data[key] = chatbot_config_update.__dict__[key]

        chatbot_config.sqlmodel_update(chatbot_config_data)
        self.session.add(chatbot_config)
        self.session.commit()
        self.session.refresh(chatbot_config)

        return chatbot_config

class ManualContextManager(EquipmentManualContextManager):

    def __init__(
        self,
        datastore_manager: Annotated[DataStoreManager, Depends()],
        data: Annotated[EquipmentManualChatBotForm | None, Depends(form_data)]=None,
        chat_id: int | None=None,
    ):
        print('chat_id is {}'.format(chat_id))
        print('data is {}'.format(data))
        chatbot_config = None
        owner = None
        title = None
        file_name = None
        collection_name = None

        if chat_id != None:
            chatbot_config = datastore_manager.get_chatbot_config(chat_id)
            owner = chatbot_config.owner
            title = chatbot_config.manual_title
            file_name = chatbot_config.file_name
            collection_name = chatbot_config.collection_name
            file_extension = file_name.split('.')[-1]
        elif data != None:
            owner = data.owner
            title = data.manual_title
            file_extension = data.file.filename.split('.')[-1]
            collection_name = data.collection_name
        
        if owner == None or title == None or file_extension == None :
            raise HTTPException(status_code=404, detail="config not found")

        
        super().__init__(
            pdf_file_path="data/manual_uploads/{}/{}.{}".format(
                owner, 
                title, 
                file_extension
            ), 
            collection_name=collection_name,
            persist_directory="data/chroma_langchain_db"
        )

class AgentManager:
    def __init__(
        self,
        chat_id: int,
        datastore_manager: Annotated[DataStoreManager, Depends()],
        context_manager: Annotated[ManualContextManager, Depends()],
        agent_wrapper: Annotated[AgentWrapper, Depends()]
    ):
        self.chat_id = chat_id
        self.datastore_manager = datastore_manager
        self.agent_wrapper = agent_wrapper
        self.context_manager = context_manager
        self.chatbot_config = datastore_manager.get_chatbot_config(chat_id)
  
    def create_agent(self):
        self.context_manager.setup_vector_store()
        self.agent_wrapper.create_agent(
            system_prompt=self.chatbot_config.system_prompt,
            tools=[self.context_manager.retrieve_context]
        )
		
    def get_response(self, user_query):
        if user_query == None:
            raise HTTPException(status_code=409, detail="no user query")
        return self.agent_wrapper.get_response(user_query)