from openai import OpenAI
from .llms import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)
gpt_3_5_turbo = "gpt-3.5-turbo"
gpt_4_o_mini = "gpt-4o-mini"

def get_response(prompt):
	response = client.chat.completions.create(
		model=gpt_4_o_mini,
		messages=[{
			"role": "user",
			"content": prompt
		}],
		temperature=0
	)
	
	return response.choices[0].message.content
	
def get_response(system_prompt, user_prompt):
	messages = [
		{"role": "system", "content": system_prompt},
		{"role": "user", "content": user_prompt}
	]
	response = client.chat.completions.create(
		model=gpt_4_o_mini,
		messages=messages,
		temperature=0
	)
	
	return response.choices[0].message.content
