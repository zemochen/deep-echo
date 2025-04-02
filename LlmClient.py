# LlmClient.py
from openai import OpenAI
import keys

def get_openai_client():
  return get_volce_engine()

def request_deep_seek(content):

  client = get_deep_seek()
  return  client.chat.completions.create(
      model="deepseek-chat",
      messages=[{"role": "system", "content": content}],
      temperature = 0.0
  )
def request_volce_engine(content):
  client = get_volce_engine()
  return client.chat.completions.create(
      model="deepseek-v3-241226",
      messages=[{"role": "system", "content": content}],
      temperature = 0.0
  )

def get_deep_seek():
  return OpenAI(
      api_key=keys.OPENAI_API_KEY,
      base_url="https://api.deepseek.com"
  )
def get_volce_engine():
  return OpenAI(
      api_key = keys.VOLCENGINE_API_KEY,
      base_url = "https://ark.cn-beijing.volces.com/api/v3",
  )