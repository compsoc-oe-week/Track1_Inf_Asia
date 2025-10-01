from openai import OpenAI

openai_api_key = "EMPTY" # This can be left alone

# Uncomment depending on where you're running this script:
# openai_api_base = "http://localhost:8000/v1" # I'm running from my local machine with SSH tunneling
openai_api_base = "http://eidf219-network-machine.vms.os.eidf.epcc.ed.ac.uk:8000/v1" # I'm running from my team's VM

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

chat_response = client.chat.completions.create(
    model="Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8",
    messages=[
        {"role": "user", "content": "Give me a short introduction to large language models."},
    ],
    max_tokens=32768,
    temperature=0.6,
    top_p=0.95,
    extra_body={
        "top_k": 20,
    },
)
print("Chat response:", chat_response)
