from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFacePipeline

template = ChatPromptTemplate.from_messages(
	[
		("system", "You are a calculator that responds with math"),	
		("human", "Answer this math question: What is two plus two?"),	
		("ai", "2+2=4"),	
		("human", "Answer this math question: {math}")
	]
)

llm = HuggingFacePipeline.from_model_id(
    model_id="crumb/nano-mistral",
    task="text-generation",
    pipeline_kwargs={"max_new_tokens": 20}
)

llm_chain = template | llm
math = "What is five plus five?"

response = llm_chain.invoke({"math": math})
print(response)
	
