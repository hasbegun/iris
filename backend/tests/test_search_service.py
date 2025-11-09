"""
Verification tests for search_service.py
Tests SearXNG Docker container integration
"""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.search_service import search_service, SearchService


async def test_searxng_connection():
    """Test 1: Verify SearXNG Docker container is accessible"""
    print("\n=== Test 1: SearXNG Connection ===")
    try:
        result = await search_service.search("test", max_results=1)
        print(f"✅ PASS: Connected to SearXNG successfully")
        print(f"   Query: '{result.query}'")
        print(f"   Results: {result.total_results}")
        return True
    except Exception as e:
        print(f"❌ FAIL: Could not connect to SearXNG")
        print(f"   Error: {e}")
        print(f"   Hint: Make sure SearXNG Docker container is running")
        print(f"         docker ps | grep searxng")
        return False


async def test_search_returns_results():
    """Test 2: Search for 'Python programming' returns results"""
    print("\n=== Test 2: Search Returns Results ===")
    try:
        result = await search_service.search("Python programming", max_results=5)

        if result.total_results > 0:
            print(f"✅ PASS: Search returned {result.total_results} results")
            print(f"\n   Top result:")
            print(f"   Title: {result.results[0].title}")
            print(f"   URL: {result.results[0].url}")
            print(f"   Content: {result.results[0].content[:100]}...")
            return True
        else:
            print(f"❌ FAIL: Search returned 0 results")
            return False

    except Exception as e:
        print(f"❌ FAIL: Search failed")
        print(f"   Error: {e}")
        return False


async def test_max_results_limit():
    """Test 3: max_results parameter limits results"""
    print("\n=== Test 3: Max Results Limit ===")
    try:
        result = await search_service.search("test query", max_results=3)

        if result.total_results <= 3:
            print(f"✅ PASS: Results limited to {result.total_results} (max: 3)")
            return True
        else:
            print(f"❌ FAIL: Returned {result.total_results} results, expected max 3")
            return False

    except Exception as e:
        print(f"❌ FAIL: Test failed")
        print(f"   Error: {e}")
        return False


async def test_disabled_service():
    """Test 4: Service gracefully handles being disabled"""
    print("\n=== Test 4: Disabled Service Handling ===")
    try:
        # Create a disabled service
        disabled_service = SearchService(enabled=False)

        try:
            await disabled_service.search("test")
            print(f"❌ FAIL: Should have raised exception when disabled")
            return False
        except Exception as e:
            if "disabled" in str(e).lower():
                print(f"✅ PASS: Service correctly raises exception when disabled")
                print(f"   Error message: {e}")
                return True
            else:
                print(f"❌ FAIL: Wrong error message")
                print(f"   Got: {e}")
                return False

    except Exception as e:
        print(f"❌ FAIL: Test failed")
        print(f"   Error: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("SEARCH SERVICE VERIFICATION TESTS")
    print("=" * 60)

    tests = [
        test_searxng_connection,
        test_search_returns_results,
        test_max_results_limit,
        test_disabled_service
    ]

    results = []
    for test in tests:
        result = await test()
        results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
