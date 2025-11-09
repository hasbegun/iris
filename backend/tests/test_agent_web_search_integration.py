"""
Quick verification test for web_search tool integration with agent
Tests that the web_search tool is properly added to the agent's toolset
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.vision_tools import create_vision_tools


def test_web_search_tool_in_agent():
    """Test: web_search tool is available in agent tools"""
    print("\n=== Web Search Tool Integration Test ===")
    try:
        # Create tools for a test session
        session_id = "test_integration_001"
        tools = create_vision_tools(session_id)

        # Get tool names
        tool_names = [t.name for t in tools]

        print(f"Available tools: {', '.join(tool_names)}")

        # Check if web_search is in the tool list
        if "web_search" in tool_names:
            print(f"✅ PASS: web_search tool successfully integrated")
            print(f"   Total tools available: {len(tools)}")

            # Find and print web_search tool details
            web_search_tool = next((t for t in tools if t.name == "web_search"), None)
            if web_search_tool:
                print(f"   Tool name: {web_search_tool.name}")
                print(f"   Description: {web_search_tool.description[:100]}...")
            return True
        else:
            print(f"❌ FAIL: web_search tool NOT found in agent tools")
            print(f"   Expected: web_search")
            print(f"   Got: {', '.join(tool_names)}")
            return False

    except Exception as e:
        print(f"❌ FAIL: Exception during test")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = test_web_search_tool_in_agent()
    sys.exit(0 if result else 1)
