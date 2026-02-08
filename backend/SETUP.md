# Backend Setup Guide

## Overview
The backend has been updated to use **Ollama (free, local LLM)** instead of paid APIs.

## Changes Made

### 1. **extractor.py**
- ✅ Renamed `MedicalExtractor` → `DocumentExtractor`
- ✅ General-purpose design (works for any domain)
- ✅ Uses Ollama instead of Anthropic Claude
- ✅ Configurable domain context (healthcare, education, retail, etc.)

### 2. **agent.py**
- ✅ Uses Ollama instead of Anthropic Claude
- ✅ No API key required

### 3. **vf_csv_parser.py**
- ✅ Uses Ollama instead of Anthropic Claude
- ✅ Works with your CSV data structure

### 4. **main.py**
- ✅ Updated imports to use `DocumentExtractor`
- ✅ Initializes extractor with healthcare domain context
- ✅ CSV upload workflow working
- ✅ Text file handling updated

### 5. **requirements.txt**
- ✅ Added `langchain-ollama`
- ✅ Removed `langchain-anthropic` and `langchain-openai`
- ✅ All dependencies are free/open-source

## Setup Instructions

### 1. Install Ollama
```bash
# Visit https://ollama.ai and download Ollama for Windows
# After installation, pull a model:
ollama pull llama3.2
```

### 2. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Setup Neo4j
- Download Neo4j Desktop or use Docker
- Create a database with credentials
- Update `.env` file:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 4. Run the Server
```bash
cd backend
python main.py
```
Or:
```bash
uvicorn main:app --reload
```

## API Endpoints

### Upload CSV
```bash
POST /upload
Content-Type: multipart/form-data
File: your_data.csv
```

### Build Knowledge Graph
```bash
POST /build-graph?clear_existing=false
```

### Query System
```bash
POST /query
{
  "query": "Which facilities lack CT scanners?",
  "show_trace": true
}
```

### Analysis
- `GET /analysis/medical-deserts`
- `GET /analysis/equipment-gaps`
- `GET /analysis/inconsistencies`
- `GET /stats`

## Domain Context

The extractor supports different domains:

**Healthcare (default):**
```python
extractor = DocumentExtractor(domain_context="healthcare")
```

**Other domains:**
```python
extractor = DocumentExtractor(domain_context="education")
extractor = DocumentExtractor(domain_context="retail")
extractor = DocumentExtractor(domain_context="general")
```

## Troubleshooting

**Ollama not found:**
- Make sure Ollama is installed and running
- Check `ollama list` to see available models
- Try `ollama pull llama3.2` if model isn't available

**Import errors:**
- Run `pip install -r requirements.txt`
- Make sure you're in the correct virtual environment

**Neo4j connection issues:**
- Verify Neo4j is running
- Check credentials in `.env` file
- Test connection: `GET /health`

## Files Structure
```
backend/
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
├── services/
│   ├── __init__.py
│   ├── extractor.py        # General-purpose entity/relationship extractor
│   ├── agent.py            # Query agent (Ollama-based)
│   ├── graph.py            # Neo4j graph operations
│   └── vf_csv_parser.py    # CSV parser (Ollama-based)
└── data/
    └── uploads/            # Uploaded files
```
