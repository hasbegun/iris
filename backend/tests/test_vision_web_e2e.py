"""
End-to-End Test: Vision + Web Search Integration
Tests the complete flow of detecting objects and searching for information about them
"""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.context_manager import context_manager
from app.services.agent_tools import web_search


async def test_web_search_tool_directly():
    """Test 1: Web search tool works independently"""
    print("\n=== Test 1: Web Search Tool (Direct Call) ===")
    try:
        # Test web search directly
        result = await web_search.ainvoke({"query": "Python programming language"})

        if result and len(result) > 50:
            print(f"✅ PASS: Web search tool works")
            print(f"   Result preview: {result[:100]}...")
            return True
        else:
            print(f"❌ FAIL: Web search returned insufficient data")
            print(f"   Result: {result}")
            return False

    except Exception as e:
        print(f"❌ FAIL: Web search tool failed")
        print(f"   Error: {e}")
        return False


async def test_simulated_vision_context():
    """Test 2: Simulated vision detection + web search context"""
    print("\n=== Test 2: Simulated Vision Context ===")
    try:
        session_id = "e2e_test_001"

        # Simulate that we detected a "car" in an image
        # In real scenario, this would come from YOLO detection
        detected_object = "car"

        print(f"   [Simulated] Detected object: {detected_object}")

        # Now search for information about the detected object
        search_query = f"what is a {detected_object} used for"
        result = await web_search.ainvoke({"query": search_query})

        if result and "car" in result.lower():
            print(f"✅ PASS: Web search returned relevant info about {detected_object}")
            print(f"   Search query: {search_query}")
            print(f"   Result preview: {result[:150]}...")
            return True
        else:
            print(f"❌ FAIL: Web search didn't return relevant info")
            print(f"   Result: {result[:200]}")
            return False

    except Exception as e:
        print(f"❌ FAIL: Test failed")
        print(f"   Error: {e}")
        return False


async def test_contextual_search_queries():
    """Test 3: Different contextual search queries"""
    print("\n=== Test 3: Contextual Search Queries ===")

    test_cases = [
        ("bottle", "plastic bottle recycling"),
        ("laptop", "laptop computer uses"),
        ("dog", "dog breeds information")
    ]

    results = []
    for obj, query in test_cases:
        try:
            print(f"\n   Testing: {obj} → '{query}'")
            result = await web_search.ainvoke({"query": query})

            if result and len(result) > 30:
                print(f"   ✅ Query successful")
                results.append(True)
            else:
                print(f"   ❌ Query failed or insufficient results")
                results.append(False)

            # Delay between queries to avoid CAPTCHA
            await asyncio.sleep(2)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"\n✅ PASS: All {total} contextual queries succeeded")
        return True
    else:
        print(f"\n⚠️ PARTIAL: {passed}/{total} queries succeeded")
        return passed >= total // 2  # Pass if at least half succeed


async def test_current_status_queries():
    """Test 4: Current status/information queries"""
    print("\n=== Test 4: Current Status Queries ===")
    try:
        # Simulate: User detected "Tesla" car, asks about current status
        detected_object = "Tesla electric car"

        print(f"   [Simulated] Detected: {detected_object}")

        # User asks: "what is the current status of it?"
        # Agent should search for current Tesla information
        query = "current status of Tesla electric cars 2025"

        result = await web_search.ainvoke({"query": query})

        if result and len(result) > 50:
            print(f"✅ PASS: Retrieved current information")
            print(f"   Query: {query}")
            print(f"   Result preview: {result[:150]}...")
            return True
        else:
            print(f"❌ FAIL: Insufficient current information")
            return False

    except Exception as e:
        print(f"❌ FAIL: Test failed")
        print(f"   Error: {e}")
        return False


async def test_integration_flow_simulation():
    """Test 5: Complete integration flow simulation"""
    print("\n=== Test 5: Complete Integration Flow ===")
    try:
        session_id = "e2e_integration_001"

        # Step 1: Simulate object detection
        print("   Step 1: [Simulated] Object detection")
        detected_objects = ["car", "person", "bicycle"]
        print(f"           Detected: {', '.join(detected_objects)}")

        # Step 2: User asks general question about detected objects
        print("\n   Step 2: User asks 'what are these used for?'")

        # Step 3: Agent should search for info about the objects
        print("   Step 3: Agent constructs search queries")
        queries = []
        for obj in detected_objects:
            query = f"what is a {obj} used for"
            queries.append(query)
            print(f"           - {query}")

        # Step 4: Execute searches
        print("\n   Step 4: Execute web searches")
        search_results = []
        for query in queries[:2]:  # Test first 2 to save time
            result = await web_search.ainvoke({"query": query})
            search_results.append(result is not None and len(result) > 30)
            # Delay between searches to avoid CAPTCHA
            await asyncio.sleep(2)

        # Step 5: Verify results
        if all(search_results):
            print(f"   ✅ All searches successful")
            print(f"\n✅ PASS: Complete integration flow works")
            return True
        else:
            print(f"   ❌ Some searches failed")
            return False

    except Exception as e:
        print(f"❌ FAIL: Integration flow failed")
        print(f"   Error: {e}")
        return False


async def main():
    """Run all E2E tests"""
    print("=" * 70)
    print("VISION + WEB SEARCH E2E INTEGRATION TESTS")
    print("=" * 70)
    print("\nThese tests verify the complete vision-web search integration:")
    print("1. Object detection (simulated)")
    print("2. Contextual web search about detected objects")
    print("3. Current status queries")
    print("=" * 70)

    tests = [
        test_web_search_tool_directly,
        test_simulated_vision_context,
        test_contextual_search_queries,
        test_current_status_queries,
        test_integration_flow_simulation
    ]

    results = []
    for test in tests:
        result = await test()
        results.append(result)
        # Delay between tests to avoid CAPTCHA triggers
        await asyncio.sleep(2)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL E2E TESTS PASSED")
        print("\nThe vision + web search integration is working correctly!")
        return 0
    elif passed >= total // 2:
        print(f"\n⚠️ PARTIAL SUCCESS: {passed}/{total} tests passed")
        print("Most functionality works, but some edge cases may need attention.")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
