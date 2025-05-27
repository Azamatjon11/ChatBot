from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.llms import OpenAI
from langchain_community.document_loaders import TextLoader
import os

# Load and index the business plan
loader = TextLoader("data/business_plan.txt", encoding="utf-8")
documents = loader.load()
splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=100)
splits = splitter.split_documents(documents)

# Create embeddings and vectorstore
embedding = OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"])
vectorstore = FAISS.from_documents(splits, embedding)
retriever = vectorstore.as_retriever()

# QA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=OpenAI(openai_api_key=os.environ["OPENAI_API_KEY"]),
    retriever=retriever
)

def get_answer(question: str) -> str:
    """
    Uses the LangChain QA chain to answer questions strictly based on the business_plan.txt file.
    If no good answer is found, responds accordingly.
    """
    question = question.strip()
    if not question:
        return "❗Please enter a question."

    try:
        # Query the QA system
        answer = qa_chain.run(question)

        # If the answer is too short or doesn't seem relevant, reject
        if not answer or "I'm not sure" in answer.lower() or len(answer.strip()) < 15:
            return "Sorry, I can only answer questions related to our business plan."

        return answer.strip()

    except Exception as e:
        print(f"❌ Error in get_answer: {e}")
        return "⚠️ Something went wrong. Please try again later."