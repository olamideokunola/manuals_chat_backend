from langgraph.prebuilt import create_react_agent
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from .utils.llms import llm_chat_open_ai

llm = llm_chat_open_ai

# Define a function to retrieve customer info by-name
@tool
def retrieve_customer_info(name: str) -> str:
    """Retrieve customer information based on their name."""
    # Filter customers for the customer's name
    #customer_info = customers[customers['name'] == name]
    return "Name: Peak Performance Co., Country: United Kingdom" #customer_info.to_string()
  
# Call the function on Peak Performance Co.
#print(retrieve_customer_info("Peak Performance Co."))

# Create a ReAct agent
agent = create_react_agent(llm, [retrieve_customer_info])
#agent = create_agent(model, tools=[retrieve_customer_info])

# Invoke the agent on the input
messages = agent.invoke({"messages": [("human", "Create a summary of our customer: Peak Performance Co.")]})
print(messages['messages'][-1].content)
