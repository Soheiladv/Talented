from google import genai
from google.genai import types

# client = genai.Client(api_key='AIzaSyD8rFjwzW_ki8IxGdMV81zZz4ZrgTB6nZc')
client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
    ),
)
print(response.text)




from IPython.display import Markdown

model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Who is the GOAT in the NBA?")

Markdown(response.text)


