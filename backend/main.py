"""
FastAPI Backend for Medical Knowledge Graph
Main application file
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


def _detail_for_error(e: Exception) -> str:
    """Turn connection-refused and similar into a clear message."""
    msg = str(e)
    if "111" in msg or "Connection refused" in msg or "ConnectionRefusedError" in msg:
        return (
            "Connection refused. "
            "Ensure Neo4j is running (default port 7687) and, for AI queries, Ollama is running (run: ollama serve). "
            "If using Docker, set NEO4J_URI=bolt://neo4j:7687 and OLLAMA_BASE_URL=http://host.docker.internal:11434 if Ollama is on the host."
        )
    return msg

from services.extractor import DocumentExtractor
from services.graph import GraphService
from services.agent import QueryAgent
from services.vf_csv_parser import VFCSVParser

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

ENV = os.environ.get("ENV", "development")
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
UPLOAD_MAX_SIZE_MB = int(os.environ.get("UPLOAD_MAX_SIZE_MB", "10"))
UPLOAD_MAX_BYTES = UPLOAD_MAX_SIZE_MB * 1024 * 1024

# Initialize services (will be set in lifespan)
extractor = None
csv_parser = None
graph_service = None
query_agent = None

# Cache for parsed data to avoid re-parsing CSV
parsed_data_cache = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    # Startup
    global extractor, csv_parser, graph_service, query_agent
    logger.info("Starting up services...")
    extractor = DocumentExtractor(domain_context="healthcare")
    csv_parser = VFCSVParser()
    graph_service = GraphService()
    query_agent = QueryAgent(graph_service)
    logger.info("Services initialized")
    
    yield
    
    # Shutdown - handle gracefully even during cancellation
    try:
        logger.info("Shutting down services...")
        if graph_service:
            graph_service.close()
        logger.info("Services closed")
    except Exception as e:
        logger.warning("Error during shutdown: %s", e)

app = FastAPI(
    title="Medical Knowledge Graph API",
    description="AI-powered medical facility intelligence system",
    version="2.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(",") if "," in CORS_ORIGINS else [CORS_ORIGINS.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class QueryRequest(BaseModel):
    query: str
    show_trace: bool = True

class QueryResponse(BaseModel):
    answer: str
    trace: Optional[dict] = None
    citations: List[str] = []

class AnalysisResponse(BaseModel):
    type: str
    results: List[dict]

class GraphStats(BaseModel):
    total_facilities: int
    total_equipment: int
    total_procedures: int
    total_specialties: int
    total_locations: int
    total_capabilities: int
    total_relationships: int

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/")
async def root():
    return {
        "service": "Medical Knowledge Graph API",
        "status": "running",
        "version": "2.0.0"
    }

@app.get("/health")
async def health_check():
    """Check if all services are operational"""
    try:
        neo4j_status = await asyncio.to_thread(graph_service.test_connection)
        
        return {
            "status": "healthy",
            "neo4j": "connected" if neo4j_status else "disconnected",
            "extractor": "ready",
            "agent": "ready"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# ============================================
# DOCUMENT PROCESSING
# ============================================

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a medical document or CSV
    Returns extracted entities and relationships
    """
    try:
        content = await file.read()
        if len(content) > UPLOAD_MAX_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {UPLOAD_MAX_SIZE_MB} MB",
            )
        os.makedirs("data/uploads", exist_ok=True)
        file_path = f"data/uploads/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Check file type
        if file.filename.endswith('.csv'):
            # Clear cache for this file to force re-parse
            if file.filename in parsed_data_cache:
                logger.info("Clearing cache for %s", file.filename)
                del parsed_data_cache[file.filename]
            
            # Use CSV parser (extracts but doesn't build graph yet)
            # LLM disabled by default for faster upload
            try:
                entities, relationships = await asyncio.to_thread(
                    csv_parser.parse_csv, file_path, False
                )
                
                # Cache the parsed data to avoid re-parsing
                parsed_data_cache[file.filename] = {
                    "entities": entities,
                    "relationships": relationships,
                    "file_path": file_path
                }
                
            except Exception as parse_error:
                logger.exception("CSV parsing error")
                import traceback
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"CSV parsing failed: {str(parse_error)}")
            
            return {
                "status": "success",
                "filename": file.filename,
                "type": "csv",
                "entities_extracted": sum(len(v) for v in entities.values()),
                "relationships_extracted": len(relationships),
                "entities": {k: len(v) for k, v in entities.items()},  # Summary only
                "sample_facilities": entities['facilities'][:3],
                "note": "Data extracted. Use POST /build-graph to populate Neo4j."
            }
        
        # Handle text files
        elif file.filename.endswith('.txt'):
            with open(file_path, 'r') as f:
                text = f.read()
            
            # Extract entities from text description
            entities = await asyncio.to_thread(
                extractor.extract_entities_from_description,
                text, 
                entity_types=["equipment", "procedures", "specialties", "services"],
                source_doc=file.filename
            )
            
            # For text files, we don't have structured data for relationships
            # Return basic entity extraction
            return {
                "status": "success",
                "filename": file.filename,
                "type": "text",
                "entities_extracted": sum(len(v) for v in entities.values()),
                "relationships_extracted": 0,
                "entities": entities,
                "relationships": [],
                "note": "Text files provide entity extraction only. Use CSV for full relationship extraction."
            }
        
        elif file.filename.endswith('.pdf'):
            # Handle PDF (you'd use pypdf here)
            raise HTTPException(501, "PDF processing not yet implemented")
        else:
            raise HTTPException(400, "Unsupported file type. Use .csv or .txt")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=_detail_for_error(e))

@app.post("/build-graph")
async def build_graph(clear_existing: bool = False, enable_llm: bool = False, force_reparse: bool = False):
    """
    Build knowledge graph from processed documents
    Set enable_llm=true to use LLM extraction (slower but more comprehensive)
    Set force_reparse=true to ignore cache and re-parse all files
    """
    try:
        if clear_existing:
            await asyncio.to_thread(graph_service.clear_graph)
        
        # Clear cache if force_reparse is true
        if force_reparse:
            logger.info("Force re-parse: clearing all cached data")
            parsed_data_cache.clear()
        
        # Dynamic entity collection - starts empty, auto-populated
        entities_all = {}
        relationships_all = []
        
        # Process all uploaded files
        upload_dir = "data/uploads"
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                file_path = os.path.join(upload_dir, filename)
                
                if filename.endswith('.csv'):
                    # Check if we have cached data for this file
                    if filename in parsed_data_cache and not enable_llm and not force_reparse:
                        logger.info("Using cached data for %s (skipping re-parse)", filename)
                        cached = parsed_data_cache[filename]
                        entities = cached["entities"]
                        rels = cached["relationships"]
                    else:
                        logger.info("Parsing %s (LLM: %s)", filename, enable_llm)
                        entities, rels = await asyncio.to_thread(
                            csv_parser.parse_csv, file_path, enable_llm
                        )
                        # Update cache
                        parsed_data_cache[filename] = {
                            "entities": entities,
                            "relationships": rels,
                            "file_path": file_path
                        }
                    
                    # Merge entities dynamically
                    for entity_type, entity_list in entities.items():
                        if entity_type not in entities_all:
                            entities_all[entity_type] = []
                        entities_all[entity_type].extend(entity_list)
                    relationships_all.extend(rels)
                
                elif filename.endswith('.txt'):
                    with open(file_path, 'r') as f:
                        text = f.read()
                    entities = await asyncio.to_thread(
                        extractor.extract_entities_from_description,
                        text,
                        entity_types=["equipment", "procedures", "specialties", "services"],
                        source_doc=filename,
                    )
                    
                    # Add to entities_all
                    for entity_type, entity_list in entities.items():
                        if entity_type in entities_all:
                            entities_all[entity_type].extend(entity_list)
        
        await asyncio.to_thread(
            graph_service.build_graph, entities_all, relationships_all
        )
        stats = await asyncio.to_thread(graph_service.get_stats)
        
        return {
            "status": "success",
            "message": "Knowledge graph built successfully",
            "stats": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=_detail_for_error(e))

# ============================================
# QUERY & ANALYSIS
# ============================================

@app.post("/query", response_model=QueryResponse)
async def query_system(request: QueryRequest):
    """
    Query the medical intelligence system
    Returns answer with reasoning trace and citations
    """
    try:
        result = await asyncio.to_thread(
            query_agent.run_query, request.query, request.show_trace
        )
        
        return QueryResponse(
            answer=result['answer'],
            trace=result.get('trace') if request.show_trace else None,
            citations=result.get('citations', [])
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=_detail_for_error(e))

@app.get("/analysis/medical-deserts", response_model=AnalysisResponse)
async def analyze_medical_deserts():
    """Find regions with insufficient medical coverage"""
    try:
        results = await asyncio.to_thread(graph_service.find_medical_deserts)
        return AnalysisResponse(type="medical_deserts", results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=_detail_for_error(e))

@app.get("/analysis/equipment-gaps", response_model=AnalysisResponse)
async def analyze_equipment_gaps():
    """Find facilities lacking critical equipment"""
    try:
        results = await asyncio.to_thread(graph_service.find_equipment_gaps)
        return AnalysisResponse(type="equipment_gaps", results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=_detail_for_error(e))

@app.get("/analysis/inconsistencies", response_model=AnalysisResponse)
async def analyze_inconsistencies():
    """Find capability inconsistencies"""
    try:
        results = await asyncio.to_thread(graph_service.find_inconsistencies)
        return AnalysisResponse(type="inconsistencies", results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=_detail_for_error(e))

# ============================================
# GRAPH STATS
# ============================================

@app.get("/stats", response_model=GraphStats)
async def get_graph_stats():
    """Get knowledge graph statistics"""
    try:
        stats = await asyncio.to_thread(graph_service.get_stats)
        return GraphStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=_detail_for_error(e))

@app.delete("/clear-graph")
async def clear_graph():
    """Clear all data from the knowledge graph"""
    try:
        await asyncio.to_thread(graph_service.clear_graph)
        return {
            "status": "success",
            "message": "Knowledge graph cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=_detail_for_error(e))

@app.get("/debug/schema")
async def debug_graph_schema():
    """Debug: Get all node labels and relationship types in the graph. Disabled in production."""
    if ENV == "production":
        raise HTTPException(status_code=404, detail="Not found")
    try:
        labels = await asyncio.to_thread(
            graph_service.query_custom, "CALL db.labels()"
        )
        relationships = await asyncio.to_thread(
            graph_service.query_custom, "CALL db.relationshipTypes()"
        )
        samples = {}
        for label_row in labels:
            label = label_row.get('label')
            if label:
                sample_query = f"MATCH (n:{label}) RETURN n LIMIT 3"
                sample_data = await asyncio.to_thread(
                    graph_service.query_custom, sample_query
                )
                samples[label] = sample_data
        
        return {
            "node_labels": [r.get('label') for r in labels],
            "relationship_types": [r.get('relationshipType') for r in relationships],
            "sample_data": samples
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=_detail_for_error(e))

# ============================================
# GRAPH VISUALIZATION
# ============================================

@app.get("/graph/visualization")
async def get_graph_visualization(limit: int = 100):
    """Get graph data for visualization (nodes and edges)"""
    try:
        graph_data = await asyncio.to_thread(
            graph_service.get_graph_visualization, limit
        )
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=_detail_for_error(e))

@app.get("/graph/query-visualization")
async def get_query_graph_visualization(query: str, limit: int = 50):
    """Get subgraph relevant to a query for visualization"""
    try:
        graph_data = await asyncio.to_thread(
            graph_service.get_query_graph, query, limit
        )
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=_detail_for_error(e))

@app.get("/graph/query-locations")
async def get_query_locations(query: str = "", limit: int = 50):
    """Get locations relevant to a query for map display (from knowledge graph)"""
    try:
        locations = await asyncio.to_thread(
            graph_service.get_query_locations, query, limit
        )
        return {"locations": locations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=_detail_for_error(e))

# ============================================
# SOURCE LOCATIONS (from uploaded CSVs)
# ============================================

def _get_locations_from_sources(query: str = "", limit: int = 100) -> list:
    """
    Read uploaded CSV files and extract facility + address data.
    Uses raw source data (not the graph) so we get full addresses for geocoding.
    """
    import pandas as pd
    results = []
    seen = set()
    # Extract keywords for filtering (skip common words)
    stop_words = {"what", "where", "which", "have", "with", "that", "this", "from", "the", "and", "are", "how"}
    keywords = [w.lower() for w in (query or "").split() if len(w) > 2 and w.lower() not in stop_words][:5]
    
    upload_dir = "data/uploads"
    if not os.path.exists(upload_dir):
        return []
    
    for filename in os.listdir(upload_dir):
        if not filename.endswith(".csv"):
            continue
        file_path = os.path.join(upload_dir, filename)
        try:
            df = pd.read_csv(file_path, low_memory=False)
        except Exception:
            continue
        
        # Expected columns (VF CSV format)
        name_col = "name" if "name" in df.columns else df.columns[0]
        city_col = "address_city" if "address_city" in df.columns else None
        state_col = "address_stateOrRegion" if "address_stateOrRegion" in df.columns else None
        country_col = "address_country" if "address_country" in df.columns else None
        country_code_col = "address_countryCode" if "address_countryCode" in df.columns else None
        addr1_col = "address_line1" if "address_line1" in df.columns else None
        
        for _, row in df.iterrows():
            facility_name = str(row.get(name_col, "")).strip()
            if not facility_name or facility_name == "nan":
                continue
            
            city = str(row.get(city_col, "")).strip() if city_col and pd.notna(row.get(city_col)) else ""
            state = str(row.get(state_col, "")).strip() if state_col and pd.notna(row.get(state_col)) else ""
            
            # Filter by query keywords if provided (match facility, city, or state)
            if keywords:
                search_text = f"{facility_name} {city} {state}".lower()
                if not any(kw in search_text for kw in keywords):
                    continue
            country = str(row.get(country_col, "Ghana")).strip() if country_col and pd.notna(row.get(country_col)) else "Ghana"
            country_code = str(row.get(country_code_col, "GH")).strip() if country_code_col and pd.notna(row.get(country_code_col)) else "GH"
            addr1 = str(row.get(addr1_col, "")).strip() if addr1_col and pd.notna(row.get(addr1_col)) else ""
            
            # Build location name (prefer full address for geocoding)
            parts = [p for p in [addr1, city, state, country] if p and p != "nan"]
            location_name = ", ".join(parts) if parts else (city or state or country or "Unknown")
            
            key = (facility_name, location_name)
            if key in seen:
                continue
            seen.add(key)
            
            results.append({
                "name": location_name,
                "city": city or "Unknown",
                "state_or_region": state or "Unknown",
                "country": country,
                "country_code": country_code,
                "facilities": [facility_name],
                "source": "csv",
            })
            
            if len(results) >= limit:
                return results
    
    return results


@app.get("/sources/locations")
async def get_source_locations(query: str = "", limit: int = 100):
    """
    Get locations from uploaded source CSVs (not the graph).
    Provides raw address data for better geocoding via Mapbox API.
    """
    try:
        locations = await asyncio.to_thread(
            _get_locations_from_sources, query, limit
        )
        return {"locations": locations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=_detail_for_error(e))

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
