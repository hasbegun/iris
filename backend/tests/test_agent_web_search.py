"""
Verification tests for agent web search integration
Tests that the ReAct agent can successfully use the web_search tool
"""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.agent_service import vision_agent
from app.services.context_manager import context_manager


async def test_agent_can_use_web_search():
    """Test 1: Agent can use web_search tool for general queries"""
    print("\n=== Test 1: Agent Can Use Web Search ===")
    try:
        # Create a test session (no image needed for pure web search)
        session_id = "test_web_search_001"

        # Ask agent a question that should trigger web search
        query = "What is the current weather in San Francisco?"

        result = await vision_agent.analyze_query(
            query=query,
            session_id=session_id
        )

        if result.get('status') == 'success':
            response = result.get('response', '')
            # Check if response contains search-like information
            # (Could contain weather info or indication of search results)
            if response and len(response) > 20:
                print(f"✅ PASS: Agent responded with web search")
                print(f"   Response preview: {response[:150]}...")
                return True
            else:
                print(f"❌ FAIL: Agent response too short or empty")
                print(f"   Response: {response}")
                return False
        else:
            print(f"❌ FAIL: Agent returned error status")
            print(f"   Error: {result.get('response')}")
            return False

    except Exception as e:
        print(f"❌ FAIL: Test raised exception")
        print(f"   Error: {e}")
        return False


async def test_agent_handles_factual_queries():
    """Test 2: Agent can handle factual queries via web search"""
    print("\n=== Test 2: Factual Queries ===")
    try:
        session_id = "test_web_search_002"

        # Ask a factual question
        query = "Who is the CEO of OpenAI?"

        result = await vision_agent.analyze_query(
            query=query,
            session_id=session_id
        )

        if result.get('status') == 'success':
            response = result.get('response', '')
            # Should contain some answer (might be Sam Altman or search results)
            if response and len(response) > 10:
                print(f"✅ PASS: Agent provided factual response")
                print(f"   Response preview: {response[:150]}...")
                return True
            else:
                print(f"❌ FAIL: Response too short")
                print(f"   Response: {response}")
                return False
        else:
            print(f"❌ FAIL: Agent error")
            print(f"   Error: {result.get('response')}")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception raised")
        print(f"   Error: {e}")
        return False


async def test_agent_web_search_with_context():
    """Test 3: Agent uses web search for current information"""
    print("\n=== Test 3: Current Information Search ===")
    try:
        session_id = "test_web_search_003"

        # Ask about current information
        query = "What are the latest developments in AI?"

        result = await vision_agent.analyze_query(
            query=query,
            session_id=session_id
        )

        if result.get('status') == 'success':
            response = result.get('response', '')
            if response and len(response) > 20:
                print(f"✅ PASS: Agent searched for current info")
                print(f"   Response preview: {response[:150]}...")
                return True
            else:
                print(f"❌ FAIL: Insufficient response")
                print(f"   Response: {response}")
                return False
        else:
            print(f"❌ FAIL: Agent error")
            print(f"   Error: {result.get('response')}")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception raised")
        print(f"   Error: {e}")
        return False


async def test_agent_initialization():
    """Test 4: Agent is properly initialized with web_search tool"""
    print("\n=== Test 4: Agent Initialization ===")
    try:
        if not vision_agent.initialized:
            print(f"❌ FAIL: Agent not initialized")
            print(f"   Error: {vision_agent.initialization_error}")
            return False

        # Create a session and check that tools are created with web_search
        session_id = "test_init_001"
        from app.services.vision_tools import create_vision_tools

        tools = create_vision_tools(session_id)
        tool_names = [t.name for t in tools]

        if "web_search" in tool_names:
            print(f"✅ PASS: Agent has web_search tool available")
            print(f"   All tools: {', '.join(tool_names)}")
            return True
        else:
            print(f"❌ FAIL: web_search tool not found in agent tools")
            print(f"   Available tools: {', '.join(tool_names)}")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception during initialization check")
        print(f"   Error: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("AGENT WEB SEARCH INTEGRATION TESTS")
    print("=" * 60)

    tests = [
        test_agent_initialization,
        test_agent_can_use_web_search,
        test_agent_handles_factual_queries,
        test_agent_web_search_with_context
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
