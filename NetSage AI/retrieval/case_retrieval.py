import os
import json
import faiss
import numpy as np
import pandas as pd
from google import genai
from google.genai import types

class CaseRetrievalEngine:
    def __init__(self, cases_csv_path="data/cases.csv", vectorstore_dir="vectorstore"):
        self.cases_csv_path = cases_csv_path
        self.vectorstore_dir = vectorstore_dir
        self.index_path = os.path.join(vectorstore_dir, "index.faiss")
        self.metadata_path = os.path.join(vectorstore_dir, "metadata.json")
        self.client = genai.Client()
        self.embedding_model = "gemini-embedding-001"
        
        self.cases_df = None
        self.index = None
        self.metadata = []
        
        self._initialize_store()

    def _initialize_store(self):
        if not os.path.exists(self.cases_csv_path):
            raise FileNotFoundError(f"Cases CSV not found at {self.cases_csv_path}")
            
        self.cases_df = pd.read_csv(self.cases_csv_path, encoding='latin-1')
        
        os.makedirs(self.vectorstore_dir, exist_ok=True)
        
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)

                if not self.metadata:
                    raise ValueError("Metadata file is empty")
            except (json.JSONDecodeError, ValueError):
                self._build_vector_store()
        else:
            self._build_vector_store()

    def _get_embedding(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.embedding_model,
            contents=text
        )
        return response.embeddings[0].values

    def _build_vector_store(self):
        embeddings = []
        self.metadata = []
        
        for idx, row in self.cases_df.iterrows():
            text_to_embed = f"Symptom: {row.get('symptom', '')} Topology: {row.get('topology_note', '')} Expected Fault: {row.get('expected_root_cause', '')}"
            
            vector = self._get_embedding(text_to_embed)
            embeddings.append(vector)
            
            self.metadata.append({
                "case_id": row.get('case_id', f"CASE-{idx}"),
                "category": row.get('category', 'General'),
                "concept_tag": row.get('Concept_Tag', row.get('concept_tag', 'General')),
                "symptom": row.get('symptom', ''),
                "expected_root_cause": row.get('expected_root_cause', ''),
                "osi_layer": row.get('osi_layer', 'Layer 3')
            })
            
        embeddings_array = np.array(embeddings).astype('float32')
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)

    def search(self, query_text: str, k: int = 3) -> list[dict]:
        """Searches the vector store for the top-k most similar cases."""
        if self.index is None or len(self.metadata) == 0:
            return []
            
        query_vector = np.array([self._get_embedding(query_text)]).astype('float32')
        distances, indices = self.index.search(query_vector, min(k, len(self.metadata)))
        
        results = []
        for rank, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                match = self.metadata[idx].copy()
                match["score"] = float(distances[0][rank])
                results.append(match)
                
        return results