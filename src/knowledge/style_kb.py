from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import hashlib
import torch
import chromadb


@dataclass
class StyleChunk:
    text: str
    chapter_num: int
    paragraph_type: str  # narrative | dialogue | scenery | poetry | inner_thought
    characters_present: List[str]
    location: str = ""
    emotional_tone: str = "neutral"


class StyleKnowledgeBase:
    """原著风格段落的向量知识库。"""

    def __init__(self, persist_dir: str = "data/knowledge_base/style"):
        self._model = None
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="style_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            self._model = SentenceTransformer("BAAI/bge-m3", device=device)
        return self._model

    def add_chunks(self, chunks: List[StyleChunk]) -> None:
        if not chunks:
            return
        texts = [c.text for c in chunks]
        embeddings = self.model.encode(texts, normalize_embeddings=True).tolist()
        ids = [
            f"ch{c.chapter_num}_{hashlib.sha256(c.text.encode()).hexdigest()[:12]}"
            for c in chunks
        ]
        metadatas = [
            {
                "chapter_num": c.chapter_num,
                "paragraph_type": c.paragraph_type,
                "characters_present": ",".join(c.characters_present),
                "location": c.location,
                "emotional_tone": c.emotional_tone,
            }
            for c in chunks
        ]
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )

    def search(
        self,
        query: str,
        paragraph_type: Optional[str] = None,
        characters: Optional[List[str]] = None,
        top_k: int = 3,
    ) -> List[str]:
        """返回与 query 最相近的原著段落文本列表。"""
        if self.count() == 0:
            return []
        query_emb = self.model.encode([query], normalize_embeddings=True).tolist()
        where: Optional[dict] = None
        if paragraph_type:
            where = {"paragraph_type": {"$eq": paragraph_type}}
        results = self.collection.query(
            query_embeddings=query_emb,
            n_results=min(top_k, self.count()),
            where=where,
            include=["documents"],
        )
        return results["documents"][0] if results["documents"] else []

    def count(self) -> int:
        return self.collection.count()
