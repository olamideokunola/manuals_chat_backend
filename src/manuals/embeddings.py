import json
import re
from typing import Any
from os import path

from .models import EquipmentManualChatBot

from ..utils.llms import llm_chat_open_ai, OPENAI_API_KEY

from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langchain.chat_models import init_chat_model
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.messages import SystemMessage, HumanMessage, AIMessage, AIMessageChunk, AnyMessage, ToolMessage

class EquipmentManualContextManager:
    
    # self.loader = None
    # self.text_splitter = None
    # self.embeddings = None
    # self.vector_store = None

    def __init__(
        self, 
        pdf_file_path: str=None, 
        model: str="text-embedding-3-large", 
        api_key: str=OPENAI_API_KEY,
        collection_name: str="example_collection",
        persist_directory: str="data/chroma_langchain_db"
    ):
        self.pdf_file_path = pdf_file_path
        self.model = model
        self.api_key = api_key
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # called here to set up embeddings for already uploaded files at run time
        self.setup_embeddings(pdf_file_path)

    def setup_embeddings(self, pdf_file_path: str):
        # enable external setup of embeddings for files after upload
        if pdf_file_path != None and path.isfile(pdf_file_path) == True:
            self.loader = PyPDFLoader(pdf_file_path)

            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200, add_start_index=True
            )

            self.embeddings = OpenAIEmbeddings(
                model=self.model,
                api_key=self.api_key
            )
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory,  # Where to save data locally, remove if not necessary
            )

    def setup_vector_store(self):
        if self.pdf_file_path != None:
            docs = self.loader.load()
            all_splits = self.text_splitter.split_documents(docs)

            self.vector_store.add_documents(documents=all_splits)
        
        self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 1},
        )

    def retrieve_context(self, query: str):
        """Retrieve information to help answer a query."""
        retrieved_docs = self.vector_store.similarity_search(query, k=1)
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\nContent: {doc.page_content}")
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs


class AgentWrapper:

    @dataclass
    class Context:
        column_name: str
		
    def __init__(self):
        self.context_manager = None
        self.agent = None
        self.system_prompt = None
	
    def create_agent(self, system_prompt: str, tools: Any):
        self.system_prompt = system_prompt
        self.agent = create_agent(
            model=llm_chat_open_ai,
            system_prompt=system_prompt,
            tools=tools,
            context_schema=AgentWrapper.Context
        )
		
    def get_response(self, user_query: str):
        print(user_query)
        messages = [
            SystemMessage(self.system_prompt),
            HumanMessage(user_query)
        ]
        for stream_mode, data in self.agent.stream( 
            {
                "messages": [
                    {"role": "system", "content": "Provide answers to questions\n\n Provide citations for the pages and sections you got answers from\n\n"},
                    {"role": "user", "content": f"{user_query}\n\n"}
                ]
            },
            stream_mode=["messages", "updates"],
        ):
            if stream_mode == "messages":
                token, metadata = data
                if isinstance(token, AIMessageChunk): #if {metadata['langgraph_node']} == 'model':
                    #yield json.dumps(token.content_blocks) + "\n"
                    for content in token.content_blocks:
                        #if "type" in content.keys() and content.type == 'text': 
                        content["content_type"] = "message_content"
						#elif "type" in content.keys() and content.type == 'tool_call_chunk': 
						#content["content_type"] = "tool_call_content"
                        yield json.dumps(content) + "\n"


            if stream_mode == "updates":
                for source, update in data.items():
                    if source in ("models", "tools"):
                        message = update["messages"][-1]
                        if isinstance(message, ToolMessage):
							#print(f"Tool response: {message.content_blocks}")
							#yield json.dumps(message.content_blocks) + "\n"
                            for content in message.content_blocks:
                                content["content_type"] = "tool_content"
                                yield json.dumps(content) + "\n"