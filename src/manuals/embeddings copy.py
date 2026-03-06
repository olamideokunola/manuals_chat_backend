import json
import re
from .utils.llms import llm_chat_open_ai, OPENAI_API_KEY

from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langchain.chat_models import init_chat_model
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.messages import SystemMessage, HumanMessage, AIMessage, AIMessageChunk, AnyMessage, ToolMessage

#print(dataset_info)

# System Prompt
SYSTEM_PROMPT = f"""
	You are a customer service agent who is also washing machine expert, providing support to customers.  You can help them troubleshoot problems.  You are very helpful and explains in simple and concise manner.
  You have access to a tool that retrieves context from the machine manual.
	Use the tool to help answer user queries.

"""


# Context
@dataclass
class Context:
	column_name: str

	
# Tools
def get_response_000(prompt_text: str):
	response = agent.invoke(
		  {"messages": [{"role": "user", "content": prompt_text}]}
	)
	return response['messages'][-1].content


# load pdf
def load_pdf():
	file_path = "/home/olamide/repos/ai-projects/maintenance/llm/data/hotpoint_manual.pdf"
	loader = PyPDFLoader(file_path)

	docs = loader.load()

	#print(len(docs))
	
	#print(docs[0].metadata)
	return docs

# split pdf text
def split():
	text_splitter = RecursiveCharacterTextSplitter(
		  chunk_size=1000, chunk_overlap=200, add_start_index=True
	)
	all_splits = text_splitter.split_documents(docs)

	#print(len(all_splits))
	return all_splits

# create embeddings
def create_embeddings():
	embeddings = OpenAIEmbeddings(
		model="text-embedding-3-large",
		api_key=OPENAI_API_KEY
	)
	return embeddings

# create vector store
def create_vector_store(embeddings):
	vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory="./data/chroma_langchain_db",  # Where to save data locally, remove if not necessary
	)
	return vector_store

# index docs
def create_index_docs(vector_store, all_splits):
	ids = vector_store.add_documents(documents=all_splits)
	return ids


def create_retriever(vector_store):
	retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 1},
	)
	return retriever


docs = load_pdf()
splits = split()
embeddings = create_embeddings()
vector_store = create_vector_store(embeddings)
ids = create_index_docs(vector_store, splits)
retriever = create_retriever(vector_store)