import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class RAGEngine:
    def __init__(self, storage_path="knowledge_base"):
        self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
        
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.documents = self.load_documents()

    def load_documents(self):
        docs = []
        for filename in os.listdir(self.storage_path):
            if filename.endswith(".txt"):
                with open(os.path.join(self.storage_path, filename), 'r', encoding='utf-8') as f:
                    docs.append({"name": filename, "content": f.read()})
        return docs

    def add_document(self, name, content):
        file_path = os.path.join(self.storage_path, f"{name}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.documents.append({"name": f"{name}.txt", "content": content})

    def search(self, query, top_k=3):
        """Simple keyword-based search for the MVP. 
        In production, we would use embeddings (OpenAI 'text-embedding-3-small')."""
        scored_docs = []
        query_words = set(query.lower().split())
        
        for doc in self.documents:
            score = sum(1 for word in query_words if word in doc['content'].lower())
            if score > 0:
                scored_docs.append((score, doc))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc[1] for doc in scored_docs[:top_k]]

    def get_response(self, prompt, system_prompt):
        context_docs = self.search(prompt)
        context_str = "\n\n".join([f"--- DOC: {d['name']} ---\n{d['content']}" for d in context_docs])
        
        full_system_prompt = system_prompt + f"\n\nCONTEXTO DOCUMENTAL:\n{context_str}"
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
