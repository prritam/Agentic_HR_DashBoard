import chromadb
import ollama
import os

class PolicyIndexer:
    def __init__(self):
        # Create a persistent database folder
        self.db_path = "./company_knowledge"
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(name="hiring_policies")

    def index_file(self, file_path):
        if not os.path.exists(file_path):
            print(f"Error: {file_path} not found.")
            return

        with open(file_path, "r") as f:
            lines = f.readlines()

        print(f"Indexing {len(lines)} policy rules...")

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Generate Embeddings (converting text to numbers)
            response = ollama.embeddings(model="llama2", prompt=line)
            embedding = response["embedding"]

            # Add to Vector Database
            self.collection.add(
                ids=[f"policy_{i}"],
                embeddings=[embedding],
                documents=[line],
                metadatas=[{"source": "policies.txt"}]
            )
        
        print("Success: Knowledge Base is ready.")

if __name__ == "__main__":
    indexer = PolicyIndexer()
    indexer.index_file("policies.txt")