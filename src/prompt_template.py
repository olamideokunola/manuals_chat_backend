from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFacePipeline

template = "Explain this concept simple and concisely: {concept}"
prompt_template = PromptTemplate.from_template(template=template)

llm = HuggingFacePipeline.from_model_id(
    model_id="crumb/nano-mistral",
    task="text-generation",
    pipeline_kwargs={"max_new_tokens": 30}
)

llm_chain = prompt_template | llm

concept = "Prompting LLMs"
print(llm_chain.invoke({"concept": concept}))
	
