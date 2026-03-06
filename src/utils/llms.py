import os
from dotenv import load_dotenv, dotenv_values
from langchain_openai import ChatOpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create an OpenAI chat LLM
llm_chat_open_ai = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)



