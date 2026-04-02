import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters.character import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_groq import ChatGroq
from langchain_classic.chains.retrieval_qa.base import RetrievalQA
from langchain_community.document_loaders import TextLoader

from llm_call import RoundRobinLLM


# ---------------------------
# CONFIG
# ---------------------------
BASE_DIR = Path(__file__).parent
DOCS_PATH = BASE_DIR / "documents"
VECTOR_DB_PATH = BASE_DIR / "vector_store"
CHROMA_PATH = BASE_DIR / "chroma_db"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ---------------------------
# RAG ENGINE CLASS
# ---------------------------
class RAGEngine:

    def __init__(self):
        self.embedding = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.vector_db = self._load_or_create_db()
        self.retriever = self.vector_db.as_retriever(search_kwargs={"k": 10})
        self.llm = RoundRobinLLM()
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.retriever,
            return_source_documents=True
        )

    # ---------------------------
    # LOAD OR CREATE VECTOR DB
    # ---------------------------

    def _load_or_create_db(self):

        if CHROMA_PATH.exists():
            print("✅ Loading existing Chroma DB...")
            return Chroma(
                persist_directory=str(CHROMA_PATH),
                embedding_function=self.embedding
            )

        print("🚀 Creating new Chroma DB...")

        documents = self._load_documents()
        chunks = self._split_documents(documents)

        db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding,
            persist_directory=str(CHROMA_PATH)
        )

        db.persist()
        return db

    # ---------------------------
    # LOAD PDF DOCUMENTS
    # ---------------------------

    def _load_documents(self):

        docs = []

        pdf_files = list(DOCS_PATH.glob("*.pdf"))
        txt_files = list(DOCS_PATH.glob("*.txt"))

        if not pdf_files and not txt_files:
            raise ValueError("❌ No PDF or TXT files found in documents folder")

        # ---------------------------
        # LOAD PDF FILES
        # ---------------------------
        for pdf in pdf_files:
            print(f"📄 Loading PDF: {pdf.name}")
            loader = PyPDFLoader(str(pdf))
            docs.extend(loader.load())

        # ---------------------------
        # LOAD TXT FILES
        # ---------------------------
        for txt in txt_files:
            print(f"📄 Loading TXT: {txt.name}")
            loader = TextLoader(str(txt), encoding="utf-8")
            docs.extend(loader.load())

        print(f"\n✅ Total Documents Loaded: {len(docs)}")

        return docs
    # ---------------------------
    # SPLIT DOCUMENTS
    # ---------------------------
    def _split_documents(self, documents):

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150
        )

        return splitter.split_documents(documents)

    # ---------------------------
    # MAIN QUERY FUNCTION
    # ---------------------------
    # def query(self, user_query: str) -> str:

    #     try:
    #         # response = self.qa_chain.invoke({"query": user_query})
    #         # return response["result"]

    #         response = self.qa_chain.invoke({"query": user_query})

    #         # ✅ Extract chunks
    #         source_docs = response.get("source_documents", [])
    
    #         print("\n🔍 Retrieved Chunks Sent to LLM:\n")
    #         for i, doc in enumerate(source_docs, 1):
    #             print(f"\n--- Chunk {i} ---")
    #             print(doc.page_content[:500])  # limit for readability

    #         # Optional: return chunks also
    #         return response["result"]





    #     except Exception as e:
    #         return f"❌ Error: {str(e)}"

    def query(self, user_query: str) -> str:

        try:
            # ---------------------------
            # STEP 1: RETRIEVE DOCUMENTS
            # ---------------------------
            # docs = self.retriever.get_relevant_documents(user_query)
            docs = self.retriever.invoke(user_query)

            print("\n🔍 Retrieved Chunks:\n")
            for i, doc in enumerate(docs, 1):
                print(f"\n--- Chunk {i} ---")
                print(doc.page_content[:500])  # preview
                print("Metadata:", doc.metadata)

            # ---------------------------
            # STEP 2: BUILD CONTEXT
            # ---------------------------
            context = "\n\n".join([doc.page_content for doc in docs])

            # ---------------------------
            # STEP 3: BUILD PROMPT (VISIBLE)
            # ---------------------------
            final_prompt = f"""
    You are an AI assistant. Answer strictly using the provided context.

    Context:
    {context}

    Question:
    {user_query}

    Instructions:
    - Do NOT hallucinate
    - If answer not in context → say "Not found in documents"
    - Be concise and professional
    """

            print("\n🧠 Final Prompt Sent to LLM:\n")
            print(final_prompt[:1500])  # avoid huge print

            # ---------------------------
            # STEP 4: LLM CALL
            # ---------------------------
            response = self.llm.invoke(final_prompt)

            return response.content

        except Exception as e:
            return f"❌ Error: {str(e)}"
# ---------------------------
# SINGLETON INSTANCE (IMPORTANT)
# ---------------------------
_rag_instance = None

def get_rag_engine():
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGEngine()
    return _rag_instance


# ---------------------------
# SIMPLE FUNCTION (USE THIS)
# ---------------------------
def ask_rag(query: str) -> str:
    engine = get_rag_engine()
    return engine.query(query)