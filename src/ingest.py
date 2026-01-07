import json
import os
import logging
import time
from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IngestionPipeline:
    def __init__(self):
        Config.validate()
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index_name = Config.INDEX_NAME
        self.namespace = Config.NAMESPACE
        self.encoder_model = Config.EMBEDDING_MODEL
        
        # Initialize Index
        self._ensure_index_exists()
        self.index = self.pc.Index(self.index_name)

    def _ensure_index_exists(self):
        existing_indexes = self.pc.list_indexes().names()
        if self.index_name not in existing_indexes:
            logger.info(f"Creating index: {self.index_name}")
            # Note: dimension 1024 is specific to llama-text-embed-v2
            self.pc.create_index(
                name=self.index_name,
                dimension=1024, 
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            while not self.pc.describe_index(self.index_name).status['ready']:
                time.sleep(1)
            logger.info("Index created and ready.")
        else:
            logger.info(f"Index {self.index_name} already exists.")

    def load_data(self):
        data_path = os.path.join(Config.DATA_DIR, "scraped_data.json")
        if not os.path.exists(data_path):
             # Fallback to text files if json doesn't exist (legacy support)
            logger.warning("scraped_data.json not found. Checking for .txt files.")
            return self._load_legacy_txt_files()
            
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_legacy_txt_files(self):
        texts = []
        for file in os.listdir(Config.DATA_DIR):
            if file.endswith(".txt"):
                with open(os.path.join(Config.DATA_DIR, file), "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        texts.append({
                            "url": "unknown", 
                            "title": file, 
                            "content": content
                        })
        return texts

    def process_and_upsert(self):
        data = self.load_data()
        if not data:
            logger.error("No data found to ingest.")
            return

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )

        all_vectors = []
        
        logger.info(f"Processing {len(data)} documents...")
        
        chunk_counter = 0
        for doc in data:
            url = doc.get("url", "unknown")
            title = doc.get("title", "unknown")
            content = doc.get("content", "")
            
            chunks = splitter.split_text(content)
            
            # Batch embedding for the current document's chunks
            # Depending on size, we might want to batch purely by number
            
            for chunk in chunks:
                all_vectors.append({
                    "id": f"doc_{chunk_counter}",
                    "text": chunk,
                    "url": url,
                    "title": title
                })
                chunk_counter += 1

        # Now embed and upsert in batches
        BATCH_SIZE = 50
        logger.info(f"Total chunks to process: {len(all_vectors)}")
        
        for i in range(0, len(all_vectors), BATCH_SIZE):
            batch = all_vectors[i:i+BATCH_SIZE]
            texts = [item["text"] for item in batch]
            
            try:
                # Embed using Pinecone Inference
                embeddings = self.pc.inference.embed(
                    model=self.encoder_model,
                    inputs=texts,
                    parameters={"input_type": "passage"}
                )
                
                vectors_to_upsert = []
                for j, emb in enumerate(embeddings):
                    item = batch[j]
                    vectors_to_upsert.append({
                        "id": item["id"],
                        "values": emb["values"],
                        "metadata": {
                            "text": item["text"],
                            "url": item["url"],
                            "title": item["title"]
                        }
                    })
                
                self.index.upsert(
                    vectors=vectors_to_upsert,
                    namespace=self.namespace
                )
                logger.info(f"Upserted batch {i // BATCH_SIZE + 1}")
                
            except Exception as e:
                logger.error(f"Error processing batch {i}: {e}")

        logger.info("Ingestion complete.")
        stats = self.index.describe_index_stats()
        logger.info(f"Index Stats: {stats}")

if __name__ == "__main__":
    pipeline = IngestionPipeline()
    pipeline.process_and_upsert()

