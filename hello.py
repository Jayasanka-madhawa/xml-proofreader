import anthropic
from dotenv import load_dotenv

load_dotenv()                    # reads .env and makes the key available

client = anthropic.Anthropic()   # finds ANTHROPIC_API_KEY as before

reply = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=100,
    messages=[{"role": "user", "content": "Say hello in five words."}],
)
print(reply.content[0].text)