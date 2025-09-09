import os
import sys
import io
from pypdf import PdfReader
import requests
import json
from requests.exceptions import Timeout, RequestException
from rouge_score import rouge_scorer
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain

def get_generated_dummy_text(api_key: str) -> str:
    """
    Generates a dummy legal document text using the Gemini API.
    """
    if not api_key:
        print("API key is not configured. Cannot generate dummy text.")
        return ""

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = (
        "Generate a short, fictitious legal contract of around 200 words. "
        "The contract should include details about parties, a purpose clause, "
        "a payment amount in USD, and a governing law clause. "
        "Keep the language simple and clear."
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status() 
        result = response.json()
        generated_text = result['candidates'][0]['content']['parts'][0]['text']
        return generated_text
    except Exception as e:
        print(f"Error generating dummy text: {e}")
        return ""

def get_document_text(pdf_source) -> str:
    """
    Extracts all text from a PDF file from a given source.
    The source can be a file path (str) or a file-like object (e.g., BytesIO).

    Args:
        pdf_source: The path to the PDF file or a file-like object.

    Returns:
        A single string containing all the text from the PDF.
    """
    print(f"--- Starting extraction ---")
    try:
        if isinstance(pdf_source, str):
            with open(pdf_source, 'rb') as file:
                reader = PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
        else:
            reader = PdfReader(pdf_source)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
            
    except FileNotFoundError:
        print(f"Error: The file at '{pdf_source}' was not found.")
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
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.7,
    )

    retriever = vector_store.as_retriever()
    
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )
    return chain

def generate_ground_truth_answers(llm_chain, questions):
    """
    Generates ground truth answers for test cases using the AI.
    """
    print("\n--- Generating ground truth answers for validation ---")
    ground_truths = []
    for q in questions:
        print(f"Generating ground truth for: {q}")
        response = llm_chain.invoke({"question": q, "chat_history": []})
        ground_truths.append(response['answer'])
    return ground_truths

def run_validation_test(conversational_chain, test_cases, api_key: str):
    """
    Runs a series of validation tests on the conversational AI chain.
    """
    if not api_key:
        print("Error: API key is not configured. Cannot run validation tests.")
        return
        
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
    
    print("\n--- Starting AI Validation Tests ---")
    
    total_score = 0
    test_results = []
    
    for i, case in enumerate(test_cases):
        print(f"\nTest Case {i+1}:")
        print(f"Question: {case['question']}")
        
        response = conversational_chain.invoke({"question": case['question'], "chat_history"
                                                : []})
        ai_answer = response['answer']
        
        scores = scorer.score(case['ground_truth'], ai_answer)
        rouge_l_score = scores['rougeL'].fmeasure
        
        total_score += rouge_l_score
        
        result_status = "PASSED" if rouge_l_score >= 0.5 else "FAILED"
        
        test_results.append({
            'question': case['question'],
            'ai_answer': ai_answer,
            'ground_truth': case['ground_truth'],
            'score': f"{rouge_l_score:.2f}",
            'status': result_status
        })
        
        print(f"AI Answer: {ai_answer}")
        print(f"Ground Truth: {case['ground_truth']}")
        print(f"ROUGE-L Score: {rouge_l_score:.2f} - Status: {result_status}")
    
    print("\n--- Validation Report ---")
    average_score = total_score / len(test_cases)
    print(f"Average ROUGE-L Score: {average_score:.2f}")
    
    for result in test_results:
        print(f"\nQuestion: {result['question']}")
        print(f"Status: {result['status']} (Score: {result['score']})")

if __name__ == "__main__":
    try:
        # Step 1: Define the questions for your test cases
        test_questions = [
            'What is the purpose of this agreement?',
            'Who are the parties in this contract?',
            'What is the amount of the payment?'
        ]

        google_api_key ="AIzaSyCu1WqC4PE1uO2VhQ5ODK22JpAUDPgNuhg"

        if not google_api_key:
            print("Error: API key is not configured. Cannot run validation tests.")
            sys.exit(1)

        # Step 2: Get document text either from user or generated by AI
        pdf_path = input("Enter the path to your PDF file (or press Enter to use a generated dummy text): ")
        if pdf_path:
            document_text = get_document_text(pdf_path)
            if not document_text:
                sys.exit(1)
        else:
            document_text = get_generated_dummy_text(google_api_key)
            if not document_text:
                print("Could not generate dummy text. Exiting.")
                sys.exit(1)
            
        print("\n--- Document for testing ---")
        print(document_text)

        # Step 3: Create the RAG pipeline
        text_chunks = get_text_chunks(document_text)
        vector_store = get_vector_store(text_chunks, google_api_key)
        conversational_chain = get_conversational_chain(vector_store, google_api_key)

        # Step 4: Dynamically generate ground truth answers
        print("\n--- Generating ground truth answers for validation ---")
        ground_truth_answers = generate_ground_truth_answers(conversational_chain, test_questions)

        # Step 5: Create a dynamic list of test cases
        dynamic_test_cases = []
        for q, a in zip(test_questions, ground_truth_answers):
            dynamic_test_cases.append({'question': q, 'ground_truth': a})

        # Step 6: Run the validation tests
        run_validation_test(conversational_chain, dynamic_test_cases, google_api_key)

    except ImportError:
        print("Required libraries not found. Please run the following command:")
        print("pip install langchain-google-genai pypdf chromadb rouge-score")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
