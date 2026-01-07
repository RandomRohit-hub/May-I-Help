# MMTT Website Assistant

The **MMTT Website Assistant** is a RAG (Retrieval-Augmented Generation) application designed to answer questions about the **Multi-Mode Tactical Tracker (MMTT)** project. It extracts knowledge from the PlayMetrics website and leverages a Vector Database (Pinecone) and a Large Language Model (Groq/Llama 3) to provide accurate, context-aware responses.

## Features

-   **Web Scraping**: Extracts text content from documentation and informational pages.
-   **RAG Pipeline**:
    -   **Vector Database**: Pinecone (Serverless) for storing and retrieving semantic embeddings.
    -   **Embeddings**: `llama-text-embed-v2`.
    -   **LLM**: Groq (`llama-3.1-8b-instant`) for fast and efficient inference.
-   **User Interface**: Streamlit-based chat interface with source attribution.
-   **Ingestion**: Automated pipeline to chunk, embed, and upsert data.

## Prerequisites

-   Python 3.8+
-   [Pinecone API Key](https://www.pinecone.io/)
-   [Groq API Key](https://console.groq.com/)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd RUFUS
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables**:
    Create a `.env` file in the root directory:
    ```env
    PINECONE_API_KEY=your_pinecone_api_key
    GROQ_API_KEY=your_groq_api_key
    ```

## Usage

### 1. Scrape Data
Run the extractor to scrape the website content.
```bash
python extracter.py
```
*Note: This will generate a `website_text.txt` file. Move this file to the `data/` directory for ingestion.*
```bash
# Windows
move website_text.txt data/

# Linux/Mac
mv website_text.txt data/
```

### 2. Ingest Data
Process the scraped data and upload embeddings to Pinecone.
```bash
python -m src.ingest
```

### 3. Run the Application
Launch the Streamlit assistant.
```bash
streamlit run app.py
```

## Project Structure

```
project
├── app.py                  # Main Streamlit application
├── extracter.py            # Web scraping script (Playwright)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (API keys)
├── data/                   # Directory for scraped text/JSON data
└── src/
    ├── config.py           # Configuration settings
    ├── ingest.py           # Data ingestion pipeline (Chunking -> Embedding -> Pinecone)
    ├── rag.py              # RAG Engine (Retrieval + Generation)
    └── scraper.py          # (Internal) Helper scraping modules
```
