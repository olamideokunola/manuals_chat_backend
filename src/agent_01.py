from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_huggingface import HuggingFacePipeline
from langchain_openai import ChatOpenAI
from wikipedia import wikipedia 

# Define the tools
tools = load_tools(["wikipedia"])

# Define the agent
agent = create_react_agent(llm, tools)

# Invoke the agent
response = agent.invoke({"messages": [("human", "How many people live in New York City?")]})
print(response['messages'][-1].content)
