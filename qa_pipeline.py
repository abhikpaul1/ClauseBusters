import os
import sys
from pypdf import PdfReader
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain

def get_vector_store(text: str, api_key: str):
    """
    Creates a vector store from document chunks.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    text_chunks = text_splitter.split_text(text)
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
    vector_store = Chroma.from_texts(text_chunks, embedding=embeddings)
    return vector_store

def get_conversational_chain(vector_store, api_key: str):
    """
    Sets up the conversational RAG chain.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=api_key)
    retriever = vector_store.as_retriever()
    
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )
    return chain

if __name__ == "__main__":
    try:
        
        google_api_key = "AIzaSyCu1WqC4PE1uO2VhQ5ODK22JpAUDPgNuhg" 

        # Get the PDF file path from the user
        pdf_path = input("Please enter the path to your PDF file: ")

        # Step 1: Extract text from the PDF
        reader = PdfReader(pdf_path)
        document_text = ""
        for page in reader.pages:
            document_text += page.extract_text() or ""
        
        # Step 2: Create a vector store
        vector_store = get_vector_store(document_text, google_api_key)
        
        # Step 3: Set up the conversational chain
        conversational_chain = get_conversational_chain(vector_store, google_api_key)
        
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
            
            response = conversational_chain({"question": user_question, "chat_history": chat_history})
            
            print("AI Answer:", response['answer'])
            chat_history.append((user_question, response['answer']))
            
    except ImportError as e:
        print("Required libraries not found. Please run the following commands:")
        print("pip install langchain-google-genai pypdf chromadb")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

