
import ollama

with open("docs/sop.txt", "r") as f:
    document = f.read()

question = "What should I do if the air pressure is too low?"

response = ollama.chat(
    model="llama3.2",
    messages=[
        {
            "role": "system",
            "content": f"Answer only using the document below. If the answer is not in the document, say 'I don't know.'\n\nDOCUMENT:\n{document}",
        },
        {"role": "user", "content": question},
    ],
)
print(response["message"]["content"])