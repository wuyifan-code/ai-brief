import sys
sys.path.insert(0, 'src')
from openai import OpenAI

client = OpenAI(
    base_url='https://api.minimaxi.com/v1',
    api_key='sk-cp-WK-OVoUJFfOlcMhybeFzooXwUnfz89J_YFL2ZBAiJP3EN66ypWx7wABcdT02I2AUkWY3aTGA72nt8-ymvqHFGXUdzBP5Frfb7C9HW6t8Eus0pt0YbQtdpB8',
)

# Test simple completion
response = client.chat.completions.create(
    model='MiniMax-M2.7',
    messages=[{'role': 'user', 'content': 'Give me a one word greeting'}],
    max_tokens=20,
    temperature=0.1,
)
print("Response:", response.choices[0].message.content)
