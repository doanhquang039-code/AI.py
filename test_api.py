"""
Test script for AI Virtual World API
Run this to verify all endpoints are working
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_endpoint(method, endpoint, data=None, description=""):
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testing: {method} {endpoint}")
    if description:
        print(f"   {description}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Success")
            result = response.json()
            print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
            return result
        else:
            print(f"   ❌ Failed")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection Error - Is the server running?")
        return None
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def main():
    print("\n" + "🤖 AI Virtual World API Test Suite")
    print(f"Testing API at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Health Check
    print_section("1. Health Check")
    test_endpoint("GET", "/", description="Root endpoint")
    test_endpoint("GET", "/api/health", description="Health check endpoint")
    
    # Test 2: Training Endpoints
    print_section("2. Training Endpoints")
    test_endpoint("GET", "/api/training/status", description="Get training status")
    
    # Start training
    training_config = {
        "algorithm": "dqn",
        "episodes": 10,
        "learning_rate": 0.001,
        "gamma": 0.99,
        "epsilon": 0.1
    }
    result = test_endpoint(
        "POST", 
        "/api/training/start", 
        data=training_config,
        description="Start training session"
    )
    
    session_id = None
    if result and "session_id" in result:
        session_id = result["session_id"]
        print(f"   Session ID: {session_id}")
    
    # Get training history
    test_endpoint("GET", "/api/training/history", description="Get training history")
    
    # Stop training if session exists
    if session_id:
        test_endpoint(
            "POST", 
            f"/api/training/stop/{session_id}",
            description="Stop training session"
        )
    
    # Test 3: Model Endpoints
    print_section("3. Model Endpoints")
    models = test_endpoint("GET", "/api/models", description="Get all models")
    
    # Test 4: Statistics Endpoints
    print_section("4. Statistics Endpoints")
    test_endpoint("GET", "/api/stats/summary", description="Get summary statistics")
    test_endpoint("GET", "/api/stats/performance", description="Get performance stats")
    
    # Test 5: Algorithm Endpoints
    print_section("5. Algorithm Endpoints")
    algorithms = test_endpoint("GET", "/api/algorithms", description="Get available algorithms")
    
    if algorithms and "algorithms" in algorithms:
        print(f"\n   Available Algorithms:")
        for algo in algorithms["algorithms"]:
            print(f"   - {algo['name']} ({algo['type']})")
    
    # Summary
    print_section("Test Summary")
    print("\n✅ All tests completed!")
    print("\nNext steps:")
    print("1. Check the results above for any failures")
    print("2. Open http://localhost:8000/docs for interactive API docs")
    print("3. Open http://localhost:4200 for the frontend")
    print("\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
