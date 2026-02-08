"""
Test script for the Intelligent Document Parser Backend
Tests all major components without requiring Neo4j
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def test_imports():
    """Test all imports"""
    print_header("TEST 1: Testing Imports")
    
    try:
        from services.extractor import DocumentExtractor
        print("✓ DocumentExtractor imported successfully")
        
        from services.agent import QueryAgent
        print("✓ QueryAgent imported successfully")
        
        from services.vf_csv_parser import VFCSVParser
        print("✓ VFCSVParser imported successfully")
        
        from services.graph import GraphService
        print("✓ GraphService imported successfully")
        
        print("\n✅ All imports successful!\n")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}\n")
        return False

def test_document_extractor():
    """Test DocumentExtractor"""
    print_header("TEST 2: Testing DocumentExtractor")
    
    try:
        from services.extractor import DocumentExtractor
        
        # Initialize extractor
        extractor = DocumentExtractor(domain_context="healthcare")
        print("✓ Extractor initialized with healthcare domain")
        
        # Test entity extraction
        test_description = """
        City Hospital is equipped with MRI scanner and X-Ray machine.
        The facility lacks CT Scanner and ventilators.
        They offer cardiology and emergency services.
        """
        
        print("\nTesting entity extraction...")
        entities = extractor.extract_entities_from_description(
            test_description,
            entity_types=["equipment", "services"],
            source_doc="test_doc"
        )
        
        print(f"Extracted entities: {json.dumps(entities, indent=2)}")
        
        # Test relationship extraction
        print("\nTesting relationship extraction...")
        relationships = extractor.extract_relationships_from_description(
            entity_name="City Hospital",
            description=test_description,
            available_entities={
                "equipment": ["MRI", "X-Ray", "CT Scanner", "Ventilator"],
                "services": ["Cardiology", "Emergency"]
            },
            source_doc="test_doc"
        )
        
        print(f"Extracted {len(relationships)} relationships:")
        for rel in relationships:
            print(f"  - {rel['source']} --[{rel['type']}]--> {rel['target']}")
        
        print("\n✅ DocumentExtractor works!\n")
        return True
    except Exception as e:
        print(f"\n❌ DocumentExtractor test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_csv_parser():
    """Test CSV Parser"""
    print_header("TEST 3: Testing CSV Parser")
    
    try:
        from services.vf_csv_parser import VFCSVParser
        import pandas as pd
        
        # Create a test CSV
        test_data = {
            'name': ['Test Hospital', 'City Clinic'],
            'specialties': ['["cardiology", "surgery"]', '["pediatrics"]'],
            'procedure': ['["Heart Surgery", "MRI Scan"]', '["Vaccination"]'],
            'equipment': ['["MRI", "X-Ray"]', '["Ultrasound"]'],
            'description': [
                'Modern hospital with advanced equipment',
                'Community clinic serving families'
            ],
            'address_city': ['Accra', 'Kumasi'],
            'address_country': ['Ghana', 'Ghana']
        }
        
        df = pd.DataFrame(test_data)
        test_csv_path = 'data/test_sample.csv'
        
        # Create data directory
        Path('data').mkdir(exist_ok=True)
        df.to_csv(test_csv_path, index=False)
        print(f"✓ Created test CSV: {test_csv_path}")
        
        # Parse CSV
        parser = VFCSVParser()
        print("✓ CSV Parser initialized")
        
        # Note: Full parsing requires LLM which may take time
        print("\n⚠️  CSV Parser ready (full parsing requires Ollama to be running)")
        print("   Run Ollama with: ollama serve")
        print("   Then test with: parser.parse_csv('data/test_sample.csv')")
        
        print("\n✅ CSV Parser initialized successfully!\n")
        return True
    except Exception as e:
        print(f"\n❌ CSV Parser test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_ollama_connection():
    """Test Ollama connection"""
    print_header("TEST 4: Testing Ollama Connection")
    
    try:
        from langchain_ollama import ChatOllama
        
        print("Attempting to connect to Ollama...")
        llm = ChatOllama(model="llama3.2", temperature=0.0)
        
        # Try a simple test
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content="Say 'Hello' in one word")])
        
        print(f"✓ Ollama response: {response.content}")
        print("\n✅ Ollama is running and working!\n")
        return True
    except Exception as e:
        print(f"\n⚠️  Ollama connection failed: {e}")
        print("\nTo fix:")
        print("  1. Make sure Ollama is installed: https://ollama.ai")
        print("  2. Start Ollama: ollama serve")
        print("  3. Pull model: ollama pull llama3.2\n")
        return False

def test_graph_service():
    """Test Graph Service (without actual Neo4j connection)"""
    print_header("TEST 5: Testing Graph Service")
    
    try:
        from services.graph import GraphService
        import os
        
        # Check environment variables
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        print(f"Neo4j URI: {neo4j_uri}")
        print(f"Neo4j User: {neo4j_user}")
        print(f"Neo4j Password: {'*' * len(neo4j_password)}")
        
        # Try to initialize (won't connect without Neo4j running)
        print("\nInitializing GraphService...")
        graph_service = GraphService()
        print("✓ GraphService initialized")
        
        # Test connection
        print("\nTesting Neo4j connection...")
        connected = graph_service.test_connection()
        
        if connected:
            print("✅ Neo4j is connected!\n")
            return True
        else:
            print("\n⚠️  Neo4j not connected")
            print("\nTo setup Neo4j:")
            print("  1. Download Neo4j Desktop or use Docker")
            print("  2. Create a database")
            print("  3. Update .env file with credentials")
            print("  4. Start the database\n")
            return False
    except Exception as e:
        print(f"\n⚠️  GraphService test failed: {e}")
        print("\nNeo4j is optional for basic functionality\n")
        return False

def test_fastapi():
    """Test FastAPI main app"""
    print_header("TEST 6: Testing FastAPI Application")
    
    try:
        import main
        print("✓ FastAPI app imported successfully")
        print(f"✓ App title: {main.app.title}")
        print(f"✓ App version: {main.app.version}")
        
        # List routes
        print("\n📍 Available API endpoints:")
        for route in main.app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = ','.join(route.methods)
                print(f"  {methods:10} {route.path}")
        
        print("\n✅ FastAPI application ready!\n")
        print("To start the server, run:")
        print("  python start.py")
        print("  OR")
        print("  uvicorn main:app --reload")
        print("\nThen visit: http://localhost:8000/docs\n")
        return True
    except Exception as e:
        print(f"\n❌ FastAPI test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "🧪 "*30)
    print("  INTELLIGENT DOCUMENT PARSER BACKEND - TEST SUITE")
    print("🧪 "*30)
    
    results = {
        "Imports": test_imports(),
        "DocumentExtractor": test_document_extractor(),
        "CSV Parser": test_csv_parser(),
        "Ollama Connection": test_ollama_connection(),
        "Graph Service": test_graph_service(),
        "FastAPI App": test_fastapi(),
    }
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "⚠️  WARN/FAIL"
        print(f"{status:15} {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Backend is ready to use!")
    elif passed >= 4:
        print("\n✨ Core functionality working! Optional services need setup.")
    else:
        print("\n⚠️  Some core tests failed. Check errors above.")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
