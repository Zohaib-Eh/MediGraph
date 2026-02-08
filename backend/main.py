"""
FastAPI Backend for Medical Knowledge Graph
Main application file
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from services.extractor import DocumentExtractor
from services.graph import GraphService
from services.agent import QueryAgent
from services.vf_csv_parser import VFCSVParser

load_dotenv()

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
    print("🚀 Starting up services...")
    extractor = DocumentExtractor(domain_context="healthcare")
    csv_parser = VFCSVParser()
    graph_service = GraphService()
    query_agent = QueryAgent(graph_service)
    print("✅ Services initialized")
    
    yield
    
    # Shutdown - handle gracefully even during cancellation
    try:
        print("🛑 Shutting down services...")
        if graph_service:
            graph_service.close()
        print("✅ Services closed")
    except Exception as e:
        print(f"⚠️  Error during shutdown: {e}")

app = FastAPI(
    title="Medical Knowledge Graph API",
    description="AI-powered medical facility intelligence system",
    version="2.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
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
        # Test Neo4j connection
        neo4j_status = graph_service.test_connection()
        
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
        # Save file
        os.makedirs("data/uploads", exist_ok=True)
        file_path = f"data/uploads/{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Check file type
        if file.filename.endswith('.csv'):
            # Clear cache for this file to force re-parse
            if file.filename in parsed_data_cache:
                print(f"🔄 Clearing cache for {file.filename}")
                del parsed_data_cache[file.filename]
            
            # Use CSV parser (extracts but doesn't build graph yet)
            # LLM disabled by default for faster upload
            try:
                entities, relationships = csv_parser.parse_csv(file_path, enable_llm=False)
                
                # Cache the parsed data to avoid re-parsing
                parsed_data_cache[file.filename] = {
                    "entities": entities,
                    "relationships": relationships,
                    "file_path": file_path
                }
                
            except Exception as parse_error:
                print(f"CSV Parsing Error: {parse_error}")
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
            entities = extractor.extract_entities_from_description(
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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/build-graph")
async def build_graph(clear_existing: bool = False, enable_llm: bool = False, force_reparse: bool = False):
    """
    Build knowledge graph from processed documents
    Set enable_llm=true to use LLM extraction (slower but more comprehensive)
    Set force_reparse=true to ignore cache and re-parse all files
    """
    try:
        if clear_existing:
            graph_service.clear_graph()
        
        # Clear cache if force_reparse is true
        if force_reparse:
            print("🔄 Force re-parse: clearing all cached data")
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
                        print(f"  ✓ Using cached data for {filename} (skipping re-parse)")
                        cached = parsed_data_cache[filename]
                        entities = cached["entities"]
                        rels = cached["relationships"]
                    else:
                        print(f"  ⚙️  Parsing {filename} (LLM: {enable_llm})...")
                        # Use CSV parser with enable_llm parameter
                        entities, rels = csv_parser.parse_csv(file_path, enable_llm=enable_llm)
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
                    # Text files only provide basic entity extraction
                    with open(file_path, 'r') as f:
                        text = f.read()
                    entities = extractor.extract_entities_from_description(
                        text,
                        entity_types=["equipment", "procedures", "specialties", "services"],
                        source_doc=filename
                    )
                    
                    # Add to entities_all
                    for entity_type, entity_list in entities.items():
                        if entity_type in entities_all:
                            entities_all[entity_type].extend(entity_list)
        
        # Build graph
        graph_service.build_graph(entities_all, relationships_all)
        
        # Get stats
        stats = graph_service.get_stats()
        
        return {
            "status": "success",
            "message": "Knowledge graph built successfully",
            "stats": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        result = query_agent.run_query(request.query, request.show_trace)
        
        return QueryResponse(
            answer=result['answer'],
            trace=result.get('trace') if request.show_trace else None,
            citations=result.get('citations', [])
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis/medical-deserts", response_model=AnalysisResponse)
async def analyze_medical_deserts():
    """Find regions with insufficient medical coverage"""
    try:
        results = graph_service.find_medical_deserts()
        return AnalysisResponse(type="medical_deserts", results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis/equipment-gaps", response_model=AnalysisResponse)
async def analyze_equipment_gaps():
    """Find facilities lacking critical equipment"""
    try:
        results = graph_service.find_equipment_gaps()
        return AnalysisResponse(type="equipment_gaps", results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis/inconsistencies", response_model=AnalysisResponse)
async def analyze_inconsistencies():
    """Find capability inconsistencies"""
    try:
        results = graph_service.find_inconsistencies()
        return AnalysisResponse(type="inconsistencies", results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# GRAPH STATS
# ============================================

@app.get("/stats", response_model=GraphStats)
async def get_graph_stats():
    """Get knowledge graph statistics"""
    try:
        stats = graph_service.get_stats()
        return GraphStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clear-graph")
async def clear_graph():
    """Clear all data from the knowledge graph"""
    try:
        graph_service.clear_graph()
        return {
            "status": "success",
            "message": "Knowledge graph cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/schema")
async def debug_graph_schema():
    """Debug: Get all node labels and relationship types in the graph"""
    try:
        labels = graph_service.query_custom("CALL db.labels()")
        relationships = graph_service.query_custom("CALL db.relationshipTypes()")
        
        # Get sample data for each node type
        samples = {}
        for label_row in labels:
            label = label_row.get('label')
            if label:
                sample_query = f"MATCH (n:{label}) RETURN n LIMIT 3"
                sample_data = graph_service.query_custom(sample_query)
                samples[label] = sample_data
        
        return {
            "node_labels": [r.get('label') for r in labels],
            "relationship_types": [r.get('relationshipType') for r in relationships],
            "sample_data": samples
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# GRAPH VISUALIZATION
# ============================================

@app.get("/graph/visualization")
async def get_graph_visualization(limit: int = 100):
    """Get graph data for visualization (nodes and edges)"""
    try:
        graph_data = graph_service.get_graph_visualization(limit)
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/query-visualization")
async def get_query_graph_visualization(query: str, limit: int = 50):
    """Get subgraph relevant to a query for visualization"""
    try:
        graph_data = graph_service.get_query_graph(query, limit)
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/query-locations")
async def get_query_locations(query: str = "", limit: int = 50):
    """Get locations relevant to a query for map display (from knowledge graph)"""
    try:
        locations = graph_service.get_query_locations(query, limit)
        return {"locations": locations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        locations = _get_locations_from_sources(query, limit)
        return {"locations": locations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
