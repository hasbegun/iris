"""
Verification tests for web_search tool in agent_tools.py
Tests the LangChain tool interface
"""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.agent_tools import web_search


async def test_tool_can_be_called():
    """Test 1: web_search tool can be invoked directly"""
    print("\n=== Test 1: Tool Can Be Called ===")
    try:
        result = await web_search.ainvoke({"query": "Python programming"})

        if result and "Search results" in result:
            print(f"✅ PASS: Tool returned search results")
            print(f"   Result preview: {result[:150]}...")
            return True
        else:
            print(f"❌ FAIL: Unexpected result format")
            print(f"   Got: {result}")
            return False

    except Exception as e:
        print(f"❌ FAIL: Tool invocation failed")
        print(f"   Error: {e}")
        return False


async def test_tool_returns_formatted_results():
    """Test 2: Tool returns well-formatted results"""
    print("\n=== Test 2: Formatted Results ===")
    try:
        result = await web_search.ainvoke({"query": "artificial intelligence"})

        # Check for key formatting elements
        has_search_query = "Search results for" in result
        has_numbered_results = "\n1. " in result
        has_urls = "URL:" in result

        if has_search_query and has_numbered_results and has_urls:
            print(f"✅ PASS: Results are properly formatted")
            print(f"   ✓ Contains search query header")
            print(f"   ✓ Contains numbered results")
            print(f"   ✓ Contains URLs")
            return True
        else:
            print(f"❌ FAIL: Results missing formatting elements")
            print(f"   Search query header: {has_search_query}")
            print(f"   Numbered results: {has_numbered_results}")
            print(f"   URLs: {has_urls}")
            print(f"\n   Result: {result[:200]}")
            return False

    except Exception as e:
        print(f"❌ FAIL: Test failed")
        print(f"   Error: {e}")
        return False


async def test_tool_handles_no_results():
    """Test 3: Tool handles queries with no results gracefully"""
    print("\n=== Test 3: No Results Handling ===")
    try:
        # Search for something very unlikely to have results
        result = await web_search.ainvoke(
            {"query": "xyzabc123nonexistentquery456789"}
        )

        # Tool should return a message, not crash
        if "No search results" in result or "Search results for" in result:
            print(f"✅ PASS: Tool handled no-results case gracefully")
            print(f"   Response: {result[:100]}")
            return True
        else:
            print(f"❌ FAIL: Unexpected response for no-results case")
            print(f"   Got: {result}")
            return False

    except Exception as e:
        print(f"❌ FAIL: Tool should handle no-results gracefully, not crash")
        print(f"   Error: {e}")
        return False


async def test_tool_metadata():
    """Test 4: Tool has proper metadata for agent"""
    print("\n=== Test 4: Tool Metadata ===")
    try:
        # Check tool name
        has_name = hasattr(web_search, 'name')
        has_description = hasattr(web_search, 'description')

        if has_name and has_description:
            print(f"✅ PASS: Tool has proper metadata")
            print(f"   Name: {web_search.name}")
            print(f"   Description: {web_search.description[:100]}...")
            return True
        else:
            print(f"❌ FAIL: Tool missing metadata")
            print(f"   Has name: {has_name}")
            print(f"   Has description: {has_description}")
            return False

    except Exception as e:
        print(f"❌ FAIL: Metadata check failed")
        print(f"   Error: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("WEB SEARCH TOOL VERIFICATION TESTS")
    print("=" * 60)

    tests = [
        test_tool_can_be_called,
        test_tool_returns_formatted_results,
        test_tool_handles_no_results,
        test_tool_metadata
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
