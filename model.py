import groq
import streamlit as st

def load_model():
    try:
        # Replace with your actual API key or use secrets
        api_key = st.secrets["groq_api_key"] if "groq_api_key" in st.secrets else "your_actual_groq_api_key_here"
        client = groq.Client(api_key=api_key)
        return client
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

def get_output(question):
    client = load_model()
    if client is None:
        return "Failed to load model."

    try:
        # Use the latest available models
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Alternative: "mixtral-8x7b-32768" is deprecated
            messages=[{"role": "user", "content": question}],
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content  
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return "Error generating response."