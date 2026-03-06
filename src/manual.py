#if __name__ == "__main__":
#	from .utils.llms import llm_chat_open_ai, OPENAI_API_KEY
#else:
#	from utils.llms import llm_chat_open_ai, OPENAI_API_KEY
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

@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    retrieved_docs = vector_store.similarity_search(query, k=1)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

# Response Format
@dataclass
class ResponseFormat:
    """Response schema for the agent."""
    # context response (always required)
    retrieve_context: str

# Agent
agent = create_agent(
    model=llm_chat_open_ai,
    system_prompt=SYSTEM_PROMPT,
    tools=[retrieve_context],
    context_schema=Context
)

async def get_response_01(user_query):
	print(user_query)
	messages = [
		SystemMessage(SYSTEM_PROMPT),
		HumanMessage(user_query)
	]
	for event in agent.stream(
		{
			"messages": [
				{"role": "system", "content": "Provide answers to questions\n\n Provide citations for the pages and sections you got answers from\n\n"},
				{"role": "user", "content": f"{user_query}\n\n"}
			]
		},
		stream_mode="values",
	):
		yield f"{event['messages'][-1]}\n\n"

def _get_source_text(content_text):
	source_regex = r'Source: \{[^}]*\}'
	source_pattern = re.compile(source_regex, re.IGNORECASE)
	source_match = source_pattern.match(content_text)
	if source_match != None: 
		print(f"pattern found is: {source_match.group()}")
		return source_match.group()


def _render_completed_message(message: AnyMessage) -> None:
	if isinstance(message, AIMessage) and message.tool_calls:
		print(f"Tool calls: {message.tool_calls}")
	if isinstance(message, ToolMessage):
		print(f"Tool response: {message.content_blocks}")
		for content in message.content_blocks:
			if "text" in content.keys():
				#print(f"{content['text']}")
				source_text = _get_source_text(content['text'])

async def get_response__(user_query):
	print(user_query)
	messages = [
		SystemMessage(SYSTEM_PROMPT),
		HumanMessage(user_query)
	]
	for stream_mode, data in agent.stream( 
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
				if token.tool_call_chunks:
					yield f"{token.tool_call_chunks}\n\n"

		if stream_mode == "updates":
			for source, update in data.items():
				if source in ("models", "tools"):
					_render_completed_message(update["messages"][-1])  

async def get_response(user_query):
	print(user_query)
	messages = [
		SystemMessage(SYSTEM_PROMPT),
		HumanMessage(user_query)
	]
	for stream_mode, data in agent.stream( 
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



async def get_response_2(user_query):
	print(user_query)
	messages = [
		SystemMessage(SYSTEM_PROMPT),
		HumanMessage(user_query)
	]
	for token, metadata in agent.stream( 
		{
			"messages": [
				{"role": "system", "content": "Provide answers to questions\n\n Provide citations for the pages and sections you got answers from.\n\n Get the page number from page_label.\n\n"},
				{"role": "user", "content": f"{user_query}\n\n"}
			]
		},
		stream_mode="messages",
	):
		if isinstance(token, AIMessageChunk): #if {metadata['langgraph_node']} == 'model':
			for content in token.content_blocks:
				if content['type'] == 'text':
					yield f"{content['text']}"
  
if __name__ == "__main__":

	"""
	results = vector_store.similarity_search(
    "What is the name of the manufacturer?"
	)

	print("results are: {}".format(results[0]))
	
	embedding = embeddings.embed_query("What is the name of the manufacturer?")

	results = vector_store.similarity_search_by_vector(embedding)
	print(results[0])
	"""
	
	query = (
		  "What is the name of the manufacturer?\n\n"
		  "Once you get the answer, mention the type of equipment this manual is for\n\n"
		  "What safety measures should I take when using the washing machine?"
		  "Provide citations for the pages and sections you got answers from"
	)
	
	for token, metadata in agent.stream(
		  {"messages": [{"role": "user", "content": query}]},
		  stream_mode="messages",
	):
		print(f"node: {metadata['langgraph_node']}")
		print(f"content: {token.content_blocks}")
		print("\n")

"""
	# Run the agent
	response = agent.invoke(
		  {"messages": [{"role": "user", "content": "What system roles can be suitable for an llm that is designed for a maintenance copilot?"}]}
	)

	#print(SYSTEM_PROMPT)
	print(response['messages'][-1].content)
"""
	

