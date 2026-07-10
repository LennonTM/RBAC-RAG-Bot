import anthropic

client = anthropic.Anthropic(api_key="your-api-key-here")

def chat():
    conversation_history = []
    print("Chatbot: Hi! Type 'quit' to exit.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break
        
        conversation_history.append({"role": "user", "content": user_input})
        
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=conversation_history
        )
        
        reply = response.content[0].text
        print("Chatbot:", reply)
        
        conversation_history.append({"role": "assistant", "content": reply})

chat()