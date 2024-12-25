from openai import OpenAI
def run_online():
    client = OpenAI(base_url='https://api.naga.ac/v1', api_key='ng-LGcMxBTm67vhTuchGZMthJ3gJxb5L')
    initial_content = input("Enter your prompt: \n")
    
    
    response = client.chat.completions.create (
        model="llama-3.1-405b-instruct",
        messages=[{'role': 'system', 'temperature': 0.1, 'content': initial_content,"max_tokens": 1000}]
    )
    
    response_content = response.choices[0].message.content
    print(response_content)
run_online()