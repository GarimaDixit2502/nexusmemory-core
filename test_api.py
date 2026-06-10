"""
AEME API Test Client
====================
Test script to verify all API endpoints are working correctly.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def test_health():
    """Test health check endpoint"""
    print_section("Testing Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✓ Health check passed")


def test_ingest():
    """Test content ingestion"""
    print_section("Testing Content Ingestion")
    
    test_docs = [
        "Machine learning is a subset of artificial intelligence.",
        "Neural networks learn patterns from data through backpropagation.",
        "Deep learning uses neural networks with multiple layers.",
        "Transformers revolutionized natural language processing.",
        "BERT is a bidirectional transformer model for language understanding."
    ]
    
    for i, doc in enumerate(test_docs, 1):
        response = requests.post(
            f"{BASE_URL}/api/ingest",
            json={"content": doc}
        )
        
        data = response.json()
        print(f"[{i}/{len(test_docs)}] Ingested: {doc[:50]}...")
        print(f"    Packet ID: {data['packet_id'][:16]}...")
        print(f"    Current MTM size: {data['current_metrics']['mtm_size']}")
        
        assert response.status_code == 200
        assert data['success'] == True
        
        time.sleep(0.2)
    
    print(f"\n✓ Ingested {len(test_docs)} documents successfully")


def test_metrics():
    """Test metrics endpoint"""
    print_section("Testing Metrics Endpoint")
    
    response = requests.get(f"{BASE_URL}/api/metrics")
    data = response.json()
    
    print("System Metrics:")
    print(f"  STM Size: {data['short_term_size']}")
    print(f"  MTM Size: {data['mid_term_size']}")
    print(f"  LTM Nodes: {data['long_term_nodes']}")
    print(f"  LTM Edges: {data['long_term_edges']}")
    print(f"  Total Processed: {data['total_packets_processed']}")
    print(f"  Consolidations: {data['consolidations_performed']}")
    
    print("\nExtraction Statistics:")
    stats = data['extraction_statistics']
    print(f"  Method: {stats.get('model', 'heuristic')}")
    print(f"  LLM Extractions: {data['llm_extractions']}")
    print(f"  Heuristic Extractions: {data['heuristic_extractions']}")
    
    assert response.status_code == 200
    print("\n✓ Metrics retrieved successfully")


def test_query():
    """Test query endpoint"""
    print_section("Testing Query Endpoint")
    
    test_queries = [
        "machine learning algorithms",
        "how do neural networks work",
        "transformer models"
    ]
    
    for query in test_queries:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={
                "query": query,
                "stm_enabled": True,
                "mtm_enabled": True,
                "ltm_enabled": True,
                "mtm_top_k": 3,
                "mtm_threshold": 0.3,
                "ltm_max_hops": 2
            }
        )
        
        data = response.json()
        
        print(f"Query: '{query}'")
        print(f"  STM Results: {len(data['stm_results'])}")
        print(f"  MTM Results: {len(data['mtm_results'])}")
        print(f"  LTM Results: {len(data['ltm_results'])}")
        print(f"  Latency: {data['metrics']['latency_ms']:.1f}ms")
        
        if data['mtm_results']:
            print(f"  Top MTM result: {data['mtm_results'][0]['content'][:60]}...")
        
        print()
        
        assert response.status_code == 200
    
    print("✓ All queries successful")


def test_consolidation():
    """Test manual consolidation"""
    print_section("Testing Manual Consolidation")
    
    # Get metrics before
    before = requests.get(f"{BASE_URL}/api/metrics").json()
    print(f"Before consolidation:")
    print(f"  MTM Size: {before['mid_term_size']}")
    print(f"  LTM Nodes: {before['long_term_nodes']}")
    
    # Trigger consolidation
    response = requests.post(
        f"{BASE_URL}/api/consolidate",
        json={"batch_size": 5}
    )
    
    data = response.json()
    print(f"\nConsolidation triggered:")
    print(f"  Packets consolidated: {data['packets_consolidated']}")
    print(f"  Message: {data['message']}")
    
    # Get metrics after
    time.sleep(0.5)
    after = requests.get(f"{BASE_URL}/api/metrics").json()
    print(f"\nAfter consolidation:")
    print(f"  MTM Size: {after['mid_term_size']}")
    print(f"  LTM Nodes: {after['long_term_nodes']} (+{after['long_term_nodes'] - before['long_term_nodes']})")
    print(f"  LTM Edges: {after['long_term_edges']} (+{after['long_term_edges'] - before['long_term_edges']})")
    
    assert response.status_code == 200
    print("\n✓ Consolidation successful")


def test_graph():
    """Test graph API endpoint"""
    print_section("Testing Graph API")
    
    response = requests.get(f"{BASE_URL}/api/graph")
    data = response.json()
    
    print(f"Graph Structure:")
    print(f"  Nodes: {len(data['nodes'])}")
    print(f"  Links: {len(data['links'])}")
    print(f"  Density: {data['stats']['density']:.3f}")
    
    if data['nodes']:
        print(f"\nSample nodes:")
        for node in data['nodes'][:5]:
            print(f"  • {node['label']} (id: {node['id']})")
    
    if data['links']:
        print(f"\nSample relationships:")
        for link in data['links'][:5]:
            print(f"  • {link['source']} --[{link['relation']}]--> {link['target']}")
    
    assert response.status_code == 200
    print("\n✓ Graph data retrieved successfully")


def run_all_tests():
    """Run all API tests"""
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  AEME API TEST SUITE".center(78) + "║")
    print("║" + "  Testing all endpoints...".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    
    try:
        test_health()
        test_ingest()
        test_metrics()
        test_query()
        test_consolidation()
        test_graph()
        
        print("\n" + "="*80)
        print("  ✅ ALL TESTS PASSED")
        print("="*80)
        print("\nYour AEME API is working perfectly!")
        print("Open http://localhost:8000 in your browser to see the dashboard.\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running first:")
    print("   python main.py\n")
    
    input("Press Enter to start tests...")
    
    run_all_tests()
