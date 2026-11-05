import ollama

response = ollama.chat(
    model="llama3.2",
    messages=[{"role": "user", "content": "Explain what an SOP is in two sentences."}],
)
print(response["message"]["content"])

