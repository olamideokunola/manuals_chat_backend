from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, File, UploadFile, Form, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlmodel import Session, col, select
from dataclasses import dataclass

import os
import shutil
import json
import jwt
from jwt.exceptions import InvalidTokenError

from .dependencies import AgentManager, ManualContextManager, SessionDep, form_data, get_session, get_chatbot_config, DataStoreManager, FileUploader

from .src.manuals.embeddings import EquipmentManualContextManager
from .auth import decode_token, get_current_user, hash_password, fake_users_db, get_current_active_user, create_access_token, authenticate_user, create_user
from .src.manuals.models import UserWithId, User, UserCreateForm, Token

print(os.getcwd())

#from .src.utils.openai import get_response
from .src.manual import get_response
from .src.manuals.db import create_db_and_tables, engine
#from .src.manuals.embeddings import AgentWrapper
from .src.manuals.models import EquipmentManualChatBot, EquipmentManualChatBotFormUpdate, EquipmentManualChatBotForm, EquipmentManualChatBotUpdate

from dotenv import load_dotenv, dotenv_values

load_dotenv()
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))



class Review(BaseModel):
	num_stars: int
	text: str
	public: bool = False

class MovieReview(BaseModel):
	movie: str
	review: Review
	
class Prompt(BaseModel):
	message_text: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    create_db_and_tables()
    yield
    # Clean up the ML models and release the resources
    


app = FastAPI(lifespan=lifespan)

# @app.on_event("startup")
# def on_startup():
# 	create_db_and_tables()


@app.get("/")
def read_root():
	return {"message": "Hello World"}
	
	
@app.get("/hello")
def hello(name: str="James"):
	return {"message": f"Hello {name}"}
	
@app.get("/prompt")
def prompt(prompt_text: str):
	print(f"prompt text is {prompt_text}")
	response = get_response(prompt_text)
	return {"message": response}
	
@app.post("/prompt")
def prompt(prompt: Prompt):
	#	print(f"prompt text is {prompt.message_text}")
	response = get_response(prompt.message_text)
	return {"message": response}


@app.post("/manual")
async def manual(prompt: Prompt):
	print(f"prompt text is {prompt.message_text}")
	return StreamingResponse(
		get_response(prompt.message_text),
		media_type="application/x-ndjson" #media_type="text/event-stream"
	)	


app.mount("/static", StaticFiles(directory="data"), name="static")
	
"""
@app.post("/reviews", response_model=DbReview)
def create_review(review: MovieReview):
	# Persist the movie review to the database
	db_review = crud.create_review(review)
	
	# Return the review including database ID
	return db_review
"""

@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
	folder_path = "data/manual_uploads"
	os.makedirs(folder_path, exist_ok=True)

	file_name = "upload.pdf"
	full_path = os.path.join(folder_path, file_name)
	with open(full_path, "wb") as f:
		file.seek(0)
		shutil.copyfileobj(file, f)
	return {"files_size": len(file)}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
	folder_path = "data/manual_uploads"
	os.makedirs(folder_path, exist_ok=True)

	file_name = file.filename
	full_path = os.path.join(folder_path, file_name)
	with open(full_path, "wb") as f:
		await file.seek(0)
		contents = await file.read()
		f.write(contents)
	return {"filename": file.filename, "content_type": file.content_type}





@app.post("/file_and_form/")
async def create_file_and_form(
	file: UploadFile,
	token: Annotated[str, Form()]
):
	folder_path = "data/manual_uploads"
	os.makedirs(folder_path, exist_ok=True)

	file_name = file.filename
	full_path = os.path.join(folder_path, file_name)
	with open(full_path, "wb") as f:
		await file.seek(0)
		contents = await file.read()
		f.write(contents)
	return {"filename": file.filename, "content_type": file.content_type, "token": token}





@app.post("/manual_config_and_upload/", response_model=EquipmentManualChatBot)
async def create_chatbot_config(
	data: Annotated[EquipmentManualChatBotForm, Form()],
	context_manager: Annotated[ManualContextManager, Depends()],
	file_uploader: Annotated[FileUploader, Depends()],
	datastore_manager: Annotated[DataStoreManager, Depends()]
):

	"""
	curl test:

	curl -F "name=Hotpoint Washing Machine ChatBot" -F "manual_title=Hotpoint Washing Machine manual" -F "equipment_type=Washing Machine" -F "chatbot_purpose=Learn to Operate and Troubleshoot" -F "owner=Me" -F "description=Testing" -F "collection_name=test_collection" -F "system_prompt=You are a customer service agent who is also washing machine expert, providing support to customers.  You can help them troubleshoot problems.  You are very helpful and explains in simple and concise manner. You have access to a tool that retrieves context from the machine manual. Use the tool to help answer user queries." -F "file=@hpt.pdf" http://localhost:8000/manual_config_and_upload/
	"""
	print('in create_chatbot_config, data is {}'.format(data))

	# check if the config with same title exists
	chatbot_config = datastore_manager.get_chatbot_config_with_title(data.manual_title)

	if chatbot_config != None:
		raise HTTPException(status_code=409, detail="config with similar title exists")

	# upload file
	await file_uploader.uploadfile()

	# create embeddings and vector store
	context_manager.setup_embeddings(file_uploader.full_path)
	context_manager.setup_vector_store()
	
	# save info to database
	manual_chatbot = datastore_manager.save_chat_config(data, file_uploader.file_name)

	return manual_chatbot


@app.get("/chats/owner/{owner}", response_model=list[EquipmentManualChatBot])
async def retrieve_chatbots(
	owner: str,
	datastore_manager: Annotated[DataStoreManager, Depends()]
):
	"""
	curl http://localhost:8000/chats/owner/Me
	"""
	chatbots = datastore_manager.get_chabot_configs_for_owner(owner)
	
	return chatbots



@app.get("/chats/{chat_id}")
async def start_chat(
	chat_id: int,
	datastore_manager: Annotated[DataStoreManager, Depends()],
	response: Response
):
	"""
	curl call:

	curl http://localhost:8000/chats/5
	"""
	chatbot_config = datastore_manager.get_chatbot_config(chat_id)
	if not chatbot_config:
		raise HTTPException(status_code=404, detail="chatbot not found")
	response.set_cookie(key="collection_name", value=chatbot_config.collection_name)
	response.set_cookie(key="owner", value=chatbot_config.owner)
	return chatbot_config

@app.patch("/chats/{chat_id}/update", response_model=EquipmentManualChatBot)
async def update_chat_config(
	chat_id: int,
	data: Annotated[EquipmentManualChatBotFormUpdate, Form()],
	file_uploader: Annotated[FileUploader, Depends()],
	datastore_manager: Annotated[DataStoreManager, Depends()]
):
	"""
	curl call:

	curl -X PATCH -F "manual_title=Washing Machine manual" -F "equipment_type=Washing Machine" http://localhost:8000/chats/5/update
	"""

	chatbot_config = datastore_manager.get_chatbot_config(chat_id)
	if not chatbot_config:
		raise HTTPException(status_code=404, detail="chatbot config not found")
	
	file_name = None

	if data.file:
		file_name = file_uploader.file_name

	chatbot_config = datastore_manager.update_chat_config(chat_id, data, file_name)

	return chatbot_config

@app.delete("/chats/{chat_id}")
async def delete_chat(
	chat_id: int, 
	datastore_manager: Annotated[DataStoreManager, Depends()]
):
	"""
	curl call:

	curl -X DELETE http://localhost:8000/chats/4
	"""
	chatbot_config = datastore_manager.get_chatbot_config(chat_id)
	
	if not chatbot_config:
		raise HTTPException(status_code=404, detail="chatbot config not found")

	datastore_manager.session.delete(chatbot_config)
	datastore_manager.session.commit()
	return {"ok": True}



@app.post("/chats/{chat_id}/user_query")
async def send_user_query(
	chat_id: int,
	user_query: Annotated[str, Form()],
	agent_manager: Annotated[AgentManager, Depends()]
):
	"""
	curl call:

	curl -F "user_query=Who are you?" http://localhost:8000/chats/1/user_query
	"""

	print("in send_user_query, chat_id is: {}.  user_query is: {}".format(chat_id, user_query))

	# Create agent
	agent_manager.create_agent()

	# Get response
	return StreamingResponse(
		agent_manager.get_response(user_query),
		media_type="application/x-ndjson" #media_type="text/event-stream"
	)

@app.post("/chats/{chat_id}/user_query_v1")
async def send_user_query_v1(
	chat_id: int,
	user_query: Annotated[str, Form()],
	agent_manager: Annotated[AgentManager, Depends()]
):
	"""
	curl call:

	curl -F "user_query=Who are you?" http://localhost:8000/chats/1/user_query
	"""

	print("in send_user_query, chat_id is: {}.  user_query is: {}".format(chat_id, user_query))

	# Create agent
	agent_manager.create_agent()

	# Get response
	return StreamingResponse(
		agent_manager.get_response(user_query),
		media_type="application/x-ndjson" #media_type="text/event-stream"
	)

# AUTHENTICATION

@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
	session: SessionDep
) -> Token:
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/")
async def read_users_me(
	session: SessionDep,
    current_user: Annotated[UserWithId, Depends(get_current_active_user)],
) -> UserWithId:
    return current_user

@app.get("/users/me/items/")
async def read_own_items(
	session: SessionDep,
    current_user: Annotated[UserWithId, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]

@app.post("/users/create")
async def create_user_account(
	data: Annotated[UserCreateForm, Form()], 
	user: Annotated[User, Depends(create_user)]
) -> Token:
	"""
	curl call:

	curl -F "username=Who are you?" -F "first_name=FirstName" -F "last_name=LastName" -F "password=testing"  http://localhost:8000/users/create
	"""
	print('form_data is: {}'.format(data))
	print('user is {}'.format(user))
	if not user:
		raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
	access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	access_token = create_access_token(
		data={"sub": user.username}, expires_delta=access_token_expires
    )
	return Token(access_token=access_token, token_type="bearer")