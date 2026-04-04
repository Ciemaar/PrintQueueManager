from pydantic_ai import Agent

agent = Agent("ollama:llama3.2", system_prompt="Hello")
print("Agent created.")
