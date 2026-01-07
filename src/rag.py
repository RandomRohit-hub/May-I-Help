from pinecone import Pinecone
from groq import Groq
from langchain_core.prompts import ChatPromptTemplate
from src.config import Config

class RAGEngine:
    def __init__(self):
        Config.validate()
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index = self.pc.Index(Config.INDEX_NAME)
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a helpful and knowledgeable website assistant. "
                "Answer the user's question ONLY using the provided context retrieved from the knowledge base. "
                "If the answer is not found in the context, say exactly: "
                "'I could not find information related to your question in the provided context.'"
                "\n\nContext:\n{context}"
            ),
            (
                "human",
                "{question}"
            )
        ])

    def retrieve(self, query):
        """Retrieve relevant docs and their metadata."""
        try:
            # Generate query embedding
            embedding = self.pc.inference.embed(
                model=Config.EMBEDDING_MODEL,
                inputs=[query],
                parameters={"input_type": "query"}
            )[0]["values"]

            # Query Pinecone
            results = self.index.query(
                vector=embedding,
                top_k=Config.TOP_K,
                include_metadata=True,
                namespace=Config.NAMESPACE
            )
            
            return results["matches"]
            
        except Exception as e:
            print(f"Retrieval Error: {e}")
            return []

    def generate_response(self, query, history=None):
        """
        Generates a response using RAG.
        Returns a dict: {'response': str, 'sources': list}
        """
        # Retrieve context
        matches = self.retrieve(query)
        
        if not matches:
            return {
                "response": "I'm sorry, I couldn't retrieve any information at the moment.",
                "sources": []
            }

        # Format context
        context_text = ""
        sources = []
        seen_urls = set()
        
        for m in matches:
            metadata = m["metadata"]
            text = metadata.get("text", "")
            url = metadata.get("url", "Unknown")
            title = metadata.get("title", "Document")
            
            context_text += f"\n--- Source: {title} ({url}) ---\n{text}\n"
            
            if url not in seen_urls and url != "Unknown":
                sources.append({"title": title, "url": url})
                seen_urls.add(url)

        # Prepare messages
        # If we had chat history, we could append it here, but for now strictly following context is safer 
        # to avoid hallucinations, though we can pass recent messages.
        # For simplicity and robustness, we treat each query mostly independently but context-aware.
        
        msg = self.prompt_template.format_messages(
            context=context_text[:Config.MAX_CONTEXT_CHARS],
            question=query
        )
        
        groq_messages = []
        for m in msg:
            groq_messages.append({"role": "user" if m.type == "human" else "system", "content": m.content})

        try:
            chat_completion = self.groq_client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=groq_messages,
                temperature=0.1, # Low temperature for factual answers
                max_tokens=1024
            )
            
            response_text = chat_completion.choices[0].message.content
            
            return {
                "response": response_text,
                "sources": sources
            }
            
        except Exception as e:
            return {
                "response": f"Error generating response: {str(e)}",
                "sources": []
            }
