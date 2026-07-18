import os
import re
from typing import List, Dict, Any, Optional

# Try importing LangChain, fallback to local equivalents if not present
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    class RecursiveCharacterTextSplitter:
        """Fallback character text splitter that splits text by chunk size and overlap."""
        def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap

        def split_text(self, text: str) -> List[str]:
            chunks = []
            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunks.append(text[start:end])
                start += self.chunk_size - self.chunk_overlap
            return chunks

        def create_documents(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[Any]:
            class Doc:
                def __init__(self, page_content, metadata):
                    self.page_content = page_content
                    self.metadata = metadata
            
            docs = []
            for i, text in enumerate(texts):
                meta = metadatas[i] if metadatas else {}
                for chunk in self.split_text(text):
                    docs.append(Doc(chunk, meta))
            return docs

# ==========================================
# High-Fidelity Local Vector Store Fallback
# ==========================================

class LocalCollection:
    """In-memory fallback matching the chromadb.Collection API."""
    def __init__(self, name: str):
        self.name = name
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.ids: List[str] = []

    def add(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        """Append document chunks and metadata records."""
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)

    def query(self, query_texts: List[str], n_results: int = 2) -> Dict[str, Any]:
        """Perform simple keyword overlap query matches."""
        query = query_texts[0].lower()
        query_words = set(re.findall(r"\b\w{3,}\b", query))
        
        matches = []
        for idx, doc in enumerate(self.documents):
            doc_lower = doc.lower()
            overlap_score = sum(1 for word in query_words if word in doc_lower)
            matches.append((overlap_score, doc, self.metadatas[idx], self.ids[idx]))

        # Sort matches by score descending
        matches.sort(key=lambda x: x[0], reverse=True)
        top_matches = matches[:n_results]

        return {
            "documents": [[m[1] for m in top_matches]],
            "metadatas": [[m[2] for m in top_matches]],
            "ids": [[m[3] for m in top_matches]]
        }


class LocalChromaClient:
    """In-memory database client matching chromadb.Client API."""
    def __init__(self):
        self.collections: Dict[str, LocalCollection] = {}

    def get_or_create_collection(self, name: str) -> LocalCollection:
        if name not in self.collections:
            self.collections[name] = LocalCollection(name)
        return self.collections[name]


# Try importing ChromaDB, fallback to local mock database client
try:
    import chromadb
    # Suppress telemetry and logs
    from chromadb.config import Settings
    chroma_client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=".chromadb_data"
    ))
except Exception:
    chroma_client = LocalChromaClient()

# ==========================================
# RAG Service Management
# ==========================================

class RAGService:
    COLLECTION_NAME = "secure_coding_guidelines"
    
    @classmethod
    def ingest_documents(cls, knowledge_base_dir: str = "knowledge_base") -> int:
        """Read all txt files in knowledge base, chunk them, and save in ChromaDB."""
        if not os.path.exists(knowledge_base_dir):
            os.makedirs(knowledge_base_dir, exist_ok=True)
            return 0

        # Fetch collection
        collection = chroma_client.get_or_create_collection(cls.COLLECTION_NAME)
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=80)
        docs_added = 0

        for file_name in os.listdir(knowledge_base_dir):
            if file_name.endswith(".txt"):
                file_path = os.path.join(knowledge_base_dir, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                    
                    # Split into character chunks
                    if hasattr(splitter, "split_text"):
                        chunks = splitter.split_text(text)
                    else:
                        chunks = [text[i:i+400] for i in range(0, len(text), 320)]

                    documents = []
                    metadatas = []
                    ids = []

                    for idx, chunk in enumerate(chunks):
                        chunk_id = f"{file_name}_{idx}"
                        documents.append(chunk)
                        metadatas.append({"source": file_name})
                        ids.append(chunk_id)

                    if documents:
                        collection.add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                        docs_added += len(documents)
                except Exception:
                    pass

        return docs_added

    @classmethod
    def retrieve_context(cls, query: str, limit: int = 2) -> str:
        """Query ChromaDB for relevant coding guidelines and return concatenated context strings."""
        try:
            collection = chroma_client.get_or_create_collection(cls.COLLECTION_NAME)
            results = collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            flat_docs = []
            if results and "documents" in results and results["documents"]:
                for sublist in results["documents"]:
                    flat_docs.extend(sublist)

            if not flat_docs:
                return ""
            
            return "\n\n---\n\n".join(flat_docs)
        except Exception as e:
            return f"Error retrieving security context: {str(e)}"
