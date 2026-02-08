"""
Quick start script for the backend server
"""
import uvicorn
import sys

if __name__ == "__main__":
    print("🚀 Starting Intelligent Document Parser API...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")
    print("🔍 Health check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        uvicorn.run(
            "main:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        sys.exit(0)
