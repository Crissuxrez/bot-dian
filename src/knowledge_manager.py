import hashlib
from pathlib import Path
from typing import List, Dict, Any
import logging
from .utils import normalize_text

logger = logging.getLogger(__name__)

class KnowledgeManager:
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or "./knowledge_base"
        self.documents = {}
        logger.info("KnowledgeManager inicializado (modo simplificado)")
    
    def add_document(self, file_path: str, metadata: Dict = None) -> str:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except:
            text = f"Archivo: {file_path.name}"
        
        text = normalize_text(text)
        doc_id = hashlib.md5(f"{file_path.name}{text[:100]}".encode()).hexdigest()
        
        if metadata is None:
            metadata = {}
        metadata.update({"filename": file_path.name, "path": str(file_path)})
        
        self.documents[doc_id] = {"text": text[:5000], "metadata": metadata}
        logger.info(f"Documento agregado: {file_path.name}")
        return doc_id
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        results = []
        query_words = query.lower().split()[:3]
        for doc_id, doc in self.documents.items():
            doc_text_lower = doc['text'].lower()
            if any(word in doc_text_lower for word in query_words):
                results.append({
                    "content": doc['text'][:500],
                    "metadata": doc['metadata'],
                    "relevance": 0.5
                })
        return results[:n_results]
    
    def list_documents(self) -> List[Dict]:
        docs = []
        seen = set()
        for doc in self.documents.values():
            filename = doc['metadata'].get('filename')
            if filename and filename not in seen:
                seen.add(filename)
                docs.append({"filename": filename, "type": "txt", "path": doc['metadata'].get('path', '')})
        return docs
    
    def remove_document(self, filename: str) -> bool:
        to_delete = []
        for doc_id, doc in self.documents.items():
            if doc['metadata'].get('filename') == filename:
                to_delete.append(doc_id)
        for doc_id in to_delete:
            del self.documents[doc_id]
        return len(to_delete) > 0
    
    def count(self) -> int:
        return len(self.documents)
