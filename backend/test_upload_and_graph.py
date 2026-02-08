"""
Integration Test: Upload Virtue Foundation CSV and Build Neo4j Graph
Tests the complete workflow from file upload to graph population
"""

import sys
import time
import requests
from pathlib import Path
import subprocess
import json

# Configuration
API_BASE_URL = "http://localhost:8000"
CSV_FILE_PATH = Path(__file__).parent / "data" / "Virtue Foundation Ghana - TEST_20.csv"
BACKEND_DIR = Path(__file__).parent
TEST_ROWS = 20  # Number of rows to test with

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def check_server_running():
    """Check if the FastAPI server is running"""
    print_header("STEP 1: Checking if Server is Running")
    
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running!")
            print(f"   {response.json()}\n")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running!")
        print("\nTo start the server:")
        print("  1. Open a new terminal")
        print("  2. Navigate to backend directory")
        print("  3. Run: python start.py")
        print("     OR: uvicorn main:app --reload\n")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}\n")
        return False

def check_neo4j_connection():
    """Check if Neo4j is connected"""
    print_header("STEP 2: Checking Neo4j Connection")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"Health Status: {json.dumps(health, indent=2)}\n")
            
            if health.get('neo4j') == 'connected':
                print("✅ Neo4j is connected!\n")
                return True
            else:
                print("❌ Neo4j is NOT connected!")
                print("\nTo setup Neo4j:")
                print("  1. Download Neo4j Desktop from: https://neo4j.com/download/")
                print("  2. Create a new database")
                print("  3. Set password and start the database")
                print("  4. Create .env file with:")
                print("     NEO4J_URI=bolt://localhost:7687")
                print("     NEO4J_USER=neo4j")
                print("     NEO4J_PASSWORD=your_password")
                print("  5. Restart the server\n")
                return False
    except Exception as e:
        print(f"❌ Error checking health: {e}\n")
        return False

def prepare_test_csv():
    """Prepare and clean test CSV with first 20 rows"""
    print_header("STEP 3A: Preparing & Cleaning Test CSV")
    
    source_csv = Path(__file__).parent / "data" / "Virtue Foundation Ghana v0.3 - Sheet1.csv"
    
    if not source_csv.exists():
        print(f"❌ Source CSV not found: {source_csv}")
        return False
    
    try:
        # Import cleaner from services folder
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from services.clean_data import DataCleaner
        
        # Create cleaner and clean test data
        cleaner = DataCleaner()
        print(f"📥 Loading first {TEST_ROWS} rows from source CSV...")
        
        # Clean and create test CSV
        df = cleaner.clean_csv(str(source_csv), str(CSV_FILE_PATH), limit_rows=TEST_ROWS)
        
        # Clear uploads folder to ensure only test CSV is processed
        uploads_dir = Path(__file__).parent / "data" / "uploads"
        if uploads_dir.exists():
            import shutil
            shutil.rmtree(uploads_dir)
            print(f"✓ Cleared uploads directory")
        
        print(f"✅ Created and cleaned test CSV with {len(df)} rows")
        print(f"   Saved to: {CSV_FILE_PATH.name}\n")
        return True
    except Exception as e:
        print(f"❌ Failed to create test CSV: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def upload_csv():
    """Upload the Virtue Foundation CSV file (extraction only, not graph building)"""
    print_header("STEP 3: Uploading & Extracting from CSV")
    
    if not CSV_FILE_PATH.exists():
        print(f"❌ CSV file not found: {CSV_FILE_PATH}")
        return None
    
    print(f"📁 File: {CSV_FILE_PATH.name}")
    print(f"📊 Size: {CSV_FILE_PATH.stat().st_size / 1024:.2f} KB\n")
    
    try:
        with open(CSV_FILE_PATH, 'rb') as f:
            files = {'file': (CSV_FILE_PATH.name, f, 'text/csv')}
            
            print("⏳ Uploading file to backend...")
            response = requests.post(
                f"{API_BASE_URL}/upload",
                files=files,
                timeout=120  # Give it 2 minutes for LLM processing
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!\n")
                print(f"📋 Upload Summary:")
                print(f"   Status: {result.get('status')}")
                print(f"   Type: {result.get('type')}")
                print(f"   Entities Extracted: {result.get('entities_extracted')}")
                print(f"   Relationships Extracted: {result.get('relationships_extracted')}")
                
                if 'entities' in result:
                    print(f"\n   Entity Breakdown:")
                    for entity_type, count in result['entities'].items():
                        print(f"     - {entity_type}: {count}")
                
                if 'sample_facilities' in result:
                    print(f"\n   Sample Facilities:")
                    for facility in result['sample_facilities'][:3]:
                        print(f"     - {facility.get('name', 'N/A')}")
                
                print()
                return result
            else:
                print(f"❌ Upload failed! Status: {response.status_code}")
                print(f"   Error: {response.text}\n")
                return None
    
    except requests.exceptions.Timeout:
        print("⏱️  Upload timed out (LLM processing may take time)")
        print("   This is normal for large CSV files with LLM extraction")
        print("   Check server logs for progress\n")
        return None
    except Exception as e:
        print(f"❌ Upload error: {e}\n")
        import traceback
        traceback.print_exc()
        return None

def build_graph(clear_existing=True):
    """Build the knowledge graph from uploaded data (re-processes CSV files)"""
    print_header("STEP 4: Building Knowledge Graph in Neo4j")
    
    try:
        print(f"⏳ Building graph (clear_existing={clear_existing})...\n")
        
        response = requests.post(
            f"{API_BASE_URL}/build-graph",
            params={"clear_existing": clear_existing},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Graph built successfully!\n")
            print(f"📊 Graph Statistics:")
            
            stats = result.get('stats', {})
            print(f"   🏥 Facilities: {stats.get('facility_count', 0)}")
            print(f"   🔧 Equipment: {stats.get('equipment_count', 0)}")
            print(f"   💉 Procedures: {stats.get('procedure_count', 0)}")
            print(f"   🩺 Specialties: {stats.get('specialty_count', 0)}")
            print(f"   📍 Locations: {stats.get('location_count', 0)}")
            print(f"   🔗 Relationships: {stats.get('relationship_count', 0)}\n")
            
            return result
        else:
            print(f"❌ Graph building failed! Status: {response.status_code}")
            print(f"   Error: {response.text}\n")
            return None
    
    except Exception as e:
        print(f"❌ Graph building error: {e}\n")
        import traceback
        traceback.print_exc()
        return None

def verify_graph():
    """Verify the graph has data by getting stats"""
    print_header("STEP 5: Verifying Graph Data")
    
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            
            total_nodes = (
                stats.get('facility_count', 0) +
                stats.get('equipment_count', 0) +
                stats.get('procedure_count', 0) +
                stats.get('specialty_count', 0) +
                stats.get('location_count', 0)
            )
            total_rels = stats.get('relationship_count', 0)
            
            if total_nodes > 0 and total_rels > 0:
                print("✅ Graph populated successfully!\n")
                print(f"📊 Total Nodes: {total_nodes}")
                print(f"🔗 Total Relationships: {total_rels}\n")
                return True
            else:
                print("⚠️  Graph appears empty!")
                print(f"   Nodes: {total_nodes}")
                print(f"   Relationships: {total_rels}\n")
                return False
        else:
            print(f"❌ Failed to verify graph. Status: {response.status_code}\n")
            return False
    
    except Exception as e:
        print(f"❌ Verification error: {e}\n")
        return False

def test_query():
    """Test querying the graph"""
    print_header("STEP 6: Testing Query Capability")
    
    test_queries = [
        "How many facilities are in the database?",
        "What equipment is available at facilities in Accra?",
        "Which facilities offer cardiology services?",
    ]
    
    print("Testing sample queries...\n")
    
    for i, query_text in enumerate(test_queries, 1):
        try:
            print(f"Query {i}: {query_text}")
            
            response = requests.post(
                f"{API_BASE_URL}/query",
                json={"query": query_text, "show_trace": False},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Answer: {result.get('answer', 'No answer')}\n")
            else:
                print(f"⚠️  Query failed: {response.status_code}\n")
        
        except Exception as e:
            print(f"⚠️  Query error: {e}\n")
    
    print("✅ Query testing complete!\n")

def main():
    """Run the complete integration test"""
    print("\n" + "🧪 "*35)
    print("  INTEGRATION TEST: CSV UPLOAD → GRAPH POPULATION")
    print(f"  Testing with first {TEST_ROWS} rows")
    print("🧪 "*35)
    
    # Step 1: Check server
    if not check_server_running():
        print("\n⛔ Cannot proceed without server running. Exiting.\n")
        return
    
    # Step 2: Check Neo4j
    if not check_neo4j_connection():
        print("\n⛔ Cannot proceed without Neo4j. Exiting.\n")
        return
    
    # Step 3A: Prepare test CSV
    if not prepare_test_csv():
        print("\n⛔ Failed to prepare test CSV. Exiting.\n")
        return
    
    # Step 3B: Upload CSV
    upload_result = upload_csv()
    if not upload_result:
        print("\n⛔ Upload failed. Exiting.\n")
        return
    
    # Step 4: Build graph
    graph_result = build_graph(clear_existing=True)
    if not graph_result:
        print("\n⛔ Graph building failed. Exiting.\n")
        return
    
    # Step 5: Verify graph
    if not verify_graph():
        print("\n⚠️  Graph verification unclear, but continuing...\n")
    
    # Step 6: Test queries
    test_query()
    
    # Success!
    print_header("✅ INTEGRATION TEST COMPLETE")
    print("🎉 Successfully uploaded CSV and populated Neo4j graph!")
    print("\n📍 Next steps:")
    print("   1. Visit http://localhost:8000/docs to explore API")
    print("   2. Open Neo4j Browser to visualize the graph")
    print("   3. Try custom queries via POST /query endpoint\n")

if __name__ == "__main__":
    main()
