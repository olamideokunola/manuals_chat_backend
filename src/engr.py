from .utils.openai import get_response, client

def delimited():
	data_structure = "pandas Dataframe"
	prompt = f"""Describe two ways that LLMs can interract with the data structure delimited with triple backticks in two paragraphs.  ```{data_structure}```"""

	response = get_response(prompt=prompt)

	print(response)

def structured_outputs():
	text = "LLMs are very useful in data analysis. But it may not be very obvious how they can be used."
	instructions = "You will be provided a text delimited by triple backticks.  Generate a title for it"
	
	output_format = """Use the following format for the output:
		- Text: <text we want to title>
		- Title: <the generated title>
	"""
	
	prompt = instructions + output_format + f"```{text}```"
	
	response = get_response(prompt=prompt)

	print(response)

def structured_outputs_table():

	prompt = "Generate a table of ten science fiction books. The columns of the table are Title, Author and Year."
	
	response = get_response(prompt=prompt)

	print(response)
	
def conditional_prompts():
	# Create the instructions
	instructions = """You will be provided with a text delimited with backticks. 
	Determine the language of the text and the number of sentences.
	If the text contains more than one sentence, generate a subtitle for it.
	Othersie write 'N/A' for the title
	"""

	# Create the output format
	output_format = """Use the following format for the output:
		  Text: <text provided>
		  Number of sentences: <number of sentences>
		  Language: <language of text>
		  Title: <title of text>
	"""
	
	text = "LLMs are very useful in data analysis. But it may not be very obvious how they can be used."

	prompt = instructions + output_format + f"```{text}```"
	response = get_response(prompt)
	print(response)

def one_shot():
	# Create a one-shot prompt
	prompt = """Extract the odd numbers from the set:
		  set: {1, 3, 7, 12, 19}
		  odd numbers: {1, 3, 7, 19}

		  set: {3, 5, 11, 12, 16}
		  odd numbers: 
	"""

	response = get_response(prompt)
	print(response)

def few_shot_01():
	messages = [
		{
			"role": "user",
			"content": "Today the weather is fantastic"	
		},
		{
			"role": "assistant",
			"content": "positive"	
		},
		{
			"role": "user",
			"content": "I don't like your attitude"	
		},
		{
			"role": "assistant",
			"content": "negative"	
		},
		{
			"role": "user",
			"content": "That shot was awful"	
		}
	]

def few_shot():
	response = client.chat.completions.create(
  model = "gpt-4o-mini",
  # Provide the examples as previous conversations
  messages = [{"role": "user", "content": "The product quality exceeded my expectations"},
              {"role": "assistant", "content": "1"},
              {"role": "user", "content": "I had a terrible experience with this product's customer service"},
              {"role": "assistant", "content": "-1"},
              # Provide the text for the model to classify
              {"role": "user", "content": "The price of the product is really fair given its features"}
             ],
		temperature = 0
	)
	print(response.choices[0].message.content)


def multi_step():
	code = '''
	def calculate_rectangle_area(length, width):
		  area = length * width
		  return area
	'''

	# Create a prompt that analyzes correctness of the code
	prompt = f"""Evaluate the code delimited with triple backticks following these steps:

	Step 1: Check for correct syntax
	Step 2: Check that it receives two inputs
	Step 3: Check that It returns one output

	This part is the multi-step prompt text: ```{code}```
	"""

	response = get_response(prompt)
	print(response)

def chain_of_thought():
	# Define the example 
	example = """Q: Sum the even numbers in the following set: {9, 10, 13, 4, 2}.
		           A: Even numbers: {10, 4, 2}. Adding them: 10+4+2=16"""

	# Define the question
	question = """Q: Sum the even numbers in the following set: {15, 13, 82, 7, 14}
		            A:"""

	# Create the final prompt
	prompt = example + question
	response = get_response(prompt)
	print(response)


def self_consistency():
	# Create the self_consistency instruction
	self_consistency_instruction = """Imagine three experts are to solve this problem delimited with triple backticks, the solution is by majority vote.
	"""

	# Create the problem to solve
	problem_to_solve = "If you own a store that sells laptops and mobile phones. You start your day with 50 devices in the store, out of which 60% are mobile phones. Throughout the day, three clients visited the store, each of them bought one mobile phone, and one of them bought additionally a laptop. Also, you added to your collection 10 laptops and 5 mobile phones. How many laptops and mobile phones do you have by the end of the day?"

	# Create the final prompt
	prompt = self_consistency_instruction + f"""```{problem_to_solve}```"""

	response = get_response(prompt)
	print(response)
	

def chat_01():
	# Purpose
	system_prompt = """You are a data analyst"""
	user_prompt = "Who are you?"
	
	print(get_response(system_prompt, user_prompt))
	
def chat_02():
	# Define the purpose of the chatbot
	chatbot_purpose = "You are a customer support chatbot for an e-commerce company specializing in electronics.  You are to assist with inquiries, order tracking, and troubleshooting."

	# Define audience guidelines
	audience_guidelines = "Your audience are tech-savvy individuals interested in purchasing electronic gadgets."

	# Define tone guidelines
	tone_guidelines = "Use a professional and user-friendly tone while interacting with customers."

	system_prompt = chatbot_purpose + audience_guidelines + tone_guidelines
	response = get_response(system_prompt, "My new headphones aren't connecting to my device")
	print(response)

if __name__ == "__main__":
	chat_02()
	
