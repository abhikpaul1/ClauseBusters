import os
import sys
from pypdf import PdfReader
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
import requests
import json
import io
from requests.exceptions import Timeout, RequestException

# Pre-load the spaCy model once for efficiency
try:
    import spacy
    NLP_MODEL = spacy.load("en_core_web_sm")
except ImportError:
    print("SpaCy library not found. Please install it.")
    sys.exit(1)
except OSError:
    print("SpaCy model not found. Please run 'python -m spacy download en_core_web_sm' to install it.")
    sys.exit(1)

def get_document_text(pdf_path: str) -> str:
    """
    Extracts all text from a PDF file from a given path.
    """
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
    except FileNotFoundError:
        print(f"Error: The file at '{pdf_path}' was not found.")
        return ""
    except Exception as e:
        print(f"An unexpected error occurred during PDF extraction: {e}")
        return ""

def get_text_chunks(text: str):
    """
    Splits a document's text into manageable chunks.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks, api_key: str):
    """
    Creates a vector store from document chunks.
    """
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
    vector_store = Chroma.from_texts(text_chunks, embedding=embeddings)
    return vector_store

def get_conversational_chain(vector_store, api_key: str):
    """
    Sets up the conversational RAG chain with safety prompts.
    """
    safety_prompt = (
        "You are a helpful legal document assistant. Your task is to answer the user's "
        "question based *only* on the provided document content. Explain the relevant "
        "clauses in a simple, jargon-free manner. Do not provide any legal advice, "
        "legal opinion, or take a legal position. "
        "If the answer is not in the document, say 'I cannot answer that question based "
        "on the provided document.'"
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.7
    )
    
    retriever = vector_store.as_retriever()
    
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )
    return chain

def summarize_text_with_gemini(text: str, api_key: str) -> str:
    """
    Calls the Gemini API to generate a summary of the provided text.
    """
    if not api_key:
        print("API key is not set. Skipping summarization.")
        return "API key not configured."

    safety_prompt = (
        "You are a helpful legal document assistant. Your task is to summarize the provided "
        "document. Explain the key clauses and agreements in a simple, jargon-free paragraph. "
        "Do not provide any legal advice, legal opinion, or take a legal position. "
        "Do not offer guidance on how to interpret or act on the document. "
    )

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.0-pro:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": safety_prompt + "Summarize the following legal document content:\n\n" + text}]}]
    }
    headers = {'Content-Type': 'application/json'}
    
    timeout_seconds = 30
    
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=timeout_seconds)
        response.raise_for_status() 
        
        result = response.json()
        
        generated_text = result['candidates'][0]['content']['parts'][0]['text']
        
        harmful_phrases = [
            "legal advice", "legal opinion", "I advise you", "I suggest you", "recommend you",
            "take this position", "your rights are", "it is my opinion that", "consult with a lawyer"
        ]
        if any(phrase in generated_text.lower() for phrase in harmful_phrases):
            return "The AI's response was flagged for containing potentially harmful content. No summary will be provided."

        return generated_text
        
    except Timeout:
        print("API call timed out.")
        return "Summarization service timed out."
    except requests.exceptions.RequestException as e:
        print(f"API call failed due to a network error: {e}")
        return "Summarization service is unavailable due to a network error."
    except (KeyError, IndexError) as e:
        print(f"Error parsing API response: The response structure was unexpected. {e}")
        return "Failed to parse API response."

def main_pipeline(pdf_path: str, api_key: str):
    """
    Main function to orchestrate the document processing pipeline.
    """
    extracted_text = get_document_text(pdf_path)
    if not extracted_text:
        return

    # Process for Q&A
    text_chunks = get_text_chunks(extracted_text)
    vector_store = get_vector_store(text_chunks, api_key)
    conversational_chain = get_conversational_chain(vector_store, api_key)
    
    print("\n--- Conversational AI is ready! ---")
    print("You can now ask questions about the document. Type 'exit' to quit.")
    
    chat_history = []
    while True:
        user_question = input("\nYour question: ")
        if user_question.lower() == 'exit':
            print("Exiting Q&A session. Goodbye!")
            break
        
        if not user_question.strip():
            continue
        
        try:
            response = conversational_chain.invoke({"question": user_question, "chat_history": chat_history})
            print("AI Answer:", response['answer'])
            chat_history.append((user_question, response['answer']))
        except Exception as e:
            print(f"An error occurred during the AI's response: {e}")
            print("Please try again or check your network connection.")


if __name__ == "__main__":
    try:
        google_api_key = "AIzaSyCu1WqC4PE1uO2VhQ5ODK22JpAUDPgNuhg"
        if not google_api_key:
            print("Error: API key is not configured. Please add your key to the script.")
            sys.exit(1)

        pdf_path = input("Please enter the path to your PDF file: ")
        if not pdf_path:
            print("No file path provided. Exiting.")
            sys.exit(1)
        
        main_pipeline(pdf_path, google_api_key)

    except ImportError:
        print("Required libraries not found. Please run the following command:")
        print("pip install langchain-google-genai pypdf chromadb")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
