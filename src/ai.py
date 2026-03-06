if __name__ == "__main__":
	from .utils.llms import llm_chat_open_ai, openai_api_key
else:
	from utils.llms import llm_chat_open_ai, openai_api_key
	
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langchain.chat_models import init_chat_model
import pandas as pd, numpy as np

data_file_path = "/home/olamide/repos/ai-projects/safetychecks/llm/data/checks_data.csv"
dataset_df = pd.read_csv(data_file_path)
print(dir(dataset_df.columns))
print(str(dataset_df.columns.to_list()))
dataset_info = str(dataset_df.columns.to_list()) #dataset_df.info().to_string()
restaurant_names = str(dataset_df['restaurant_name'].drop_duplicates().to_list())

print(restaurant_names)

#print(dataset_info)

# System Prompt
SYSTEM_PROMPT = f"""You are an expert data analyst, who provides anwers to users based on your knowledge of the dataset of restaurants and their food safety checks.  The dataset is a pandas dataframe. 

The list of column names of the dataframe is delimited with triple backticks as follows: ```{dataset_info}```.  

The list of restaurant names if delimited with triple backticks as follows: ```{restaurant_names}```.

You have access these tools:

- get_number_of_restaurants: use this tool to get number of restaurants in the dataset	
- get_number_of_checks: use this tool to get the number of checks using the appropriate column name selected from the delimited column names in triple backticks.
- get_number_of_restaurant_checks: use this tool to get the number of a type of checks done by a restaurant
- get_number_of_restaurant_checks_on_date: use this tool to get the number of a type of checks for a restaurant on a particular date
- check_date: use this tool to check if there any records for the date 
- get_check_dates_for_restaurant: use this tool to get days that a restaurant carried out a check

You can use the name of the columns to answer questions regarding the checks.

If there is a request for number of checks, obtain the column name for the type of check from the column names.

If there is a request for the number of a type of check done by a particular restaurant, obtain the restaurant name from list of restaurants and use it to get the number of the type of check for the restaurant.

When your response involves names of many restaurants, ensure at all restaurants that meet the that answer the question are listed.  

When your reponse involves types checks, ensure relevant check types are listed as defined in the column names.

If you need to make a request that uses a date, write the date as a string in this format: yyyy-mm-dd

If the reponse involves two checks that are similar in name, list them separately.

If there are no records for a date, respond that the request cannot be answered because there no records on that date.

"""



# Context
@dataclass
class Context:
	column_name: str
	
# Tools
@tool
def get_number_of_restaurants() -> int:
    """Get number of restaurants"""
    
    #print(dir(df))
    #print(df['restaurant_name'].count())
    #print(df['restaurant_name'].drop_duplicates().count())
    return dataset_df['restaurant_name'].drop_duplicates().count()

@tool
def get_number_of_checks(column_name: str) -> int:
    """Get number of checks using a column name for a column that contains data about number of checks"""
    return dataset_df[column_name].sum()

@tool
def get_number_of_restaurant_checks(column_name: str, restaurant_name: str) -> int:
    """get the number of a type of checks for a restaurant using a column name
    
    Args:
        column_name: Column name that represents type of check
        restaurant_name: Restaurant to filter for
    """
    is_this_restaurant = dataset_df['restaurant_name'] == restaurant_name
    return dataset_df[is_this_restaurant][column_name].sum()

@tool
def get_number_of_restaurant_checks_on_date(column_name: str, restaurant_name: str, check_date: str) -> int:
    """get the number of a type of checks on a date for a restaurant using a column name
    
    Args:
        column_name: Column name that represents type of check
        restaurant_name: Restaurant to filter for
        check_date: Date of check to filter for
    """

    is_this_restaurant = dataset_df['restaurant_name'] == restaurant_name
    is_on_date = dataset_df['date'] == check_date
    is_both = np.logical_and(is_this_restaurant, is_on_date)
    return dataset_df[is_both][column_name].sum()

@tool
def check_date(check_date: str) -> bool:
    """checks if there are any records for a date
    
    Args:
        check_date: Date to check for
    """

    date_found = dataset_df['date'].count() > 0

    return date_found

@tool
def get_check_dates_for_restaurant(restaurant_name: str) -> str:
    """Gets the dates a restaurant carried out checks
    
    Args:
        restaurant_name: restaurant name to filter with
    """
    is_this_restaurant = dataset_df['restaurant_name'] == restaurant_name
    dates = dataset_df[is_this_restaurant]['date']
    dates_str =  ', '.join(dates.to_list())

    return dates_str

# Agent
agent = create_agent(
    model=llm_chat_open_ai,
    system_prompt=SYSTEM_PROMPT,
    tools=[
    	get_number_of_restaurants, 
    	get_number_of_checks, 
    	get_number_of_restaurant_checks, 
    	get_number_of_restaurant_checks_on_date,
    	get_check_dates_for_restaurant
  	],
    context_schema=Context
)

def get_response(prompt_text: str):
	response = agent.invoke(
		  {"messages": [{"role": "user", "content": prompt_text}]}
	)
	return response['messages'][-1].content


if __name__ == "__main__":
	#get_number_of_restaurants()
	#print("Number of checks is {}".format(get_number_of_checks("Cooking-NumberOfChecks")))
	#print(get_number_of_restaurant_checks("Cooking-NumberOfChecks", "Boardwalk"))
	# get_check_dates_for_restaurant("Tiffany")
	
	
	# Run the agent
	response = agent.invoke(
		  {"messages": [{"role": "user", "content": "Summarise all the checks done by Tiffany Yesterday"}]}
	)

	#print(SYSTEM_PROMPT)
	print(response['messages'][-1].content)
	
	
	
	

