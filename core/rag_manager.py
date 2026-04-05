import chromadb
import ollama

class RAGManager:
    def __init__(self):
        # Initialize the local vector database
        self.client = chromadb.PersistentClient(path="./company_knowledge")
        self.collection = self.client.get_or_create_collection(name="hiring_policies")

    def add_policy(self, text, metadata):
        # Convert text to a vector (embedding) using Ollama
        response = ollama.embeddings(model="llama2", prompt=text)
        embedding = response["embedding"]
        
        self.collection.add(
            ids=[metadata["id"]],
            embeddings=[embedding],
            documents=[text]
        )

    def query_policy(self, query_text):
        # Search the database for the most relevant policy
        query_emb = ollama.embeddings(model="llama2", prompt=query_text)["embedding"]
        results = self.collection.query(query_embeddings=[query_emb], n_results=2)
        return results["documents"]