#!/usr/bin/env python3
"""
Complete Web Search Feature Test Suite
Runs all tests in sequence with detailed reporting
"""
import subprocess
import sys
import os
from datetime import datetime

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(80)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")


def print_test_header(test_name, phase):
    """Print test section header"""
    print(f"\n{BOLD}[{phase}] {test_name}{RESET}")
    print(f"{'-' * 80}")


def run_test(test_file, test_name, phase):
    """Run a single test file and return success status"""
    print_test_header(test_name, phase)

    try:
        # Run the test
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Print output
        print(result.stdout)
        if result.stderr:
            print(f"{YELLOW}Warnings:{RESET}")
            print(result.stderr)

        # Check result
        if result.returncode == 0:
            print(f"\n{GREEN}✅ {test_name}: PASSED{RESET}")
            return True
        else:
            print(f"\n{RED}❌ {test_name}: FAILED{RESET}")
            return False

    except subprocess.TimeoutExpired:
        print(f"\n{RED}❌ {test_name}: TIMEOUT (>30s){RESET}")
        return False
    except Exception as e:
        print(f"\n{RED}❌ {test_name}: ERROR - {e}{RESET}")
        return False


def check_services():
    """Check if required services are running"""
    print_header("SERVICE HEALTH CHECK")

    services = {
        "SearXNG": ("http://localhost:9090/", "Web search engine"),
        "ML Service": ("http://localhost:9001/health", "Object detection"),
        "Backend": ("http://localhost:9000/api/health", "Main API")
    }

    all_healthy = True

    for name, (url, desc) in services.items():
        try:
            import urllib.request
            response = urllib.request.urlopen(url, timeout=2)
            status = response.getcode()

            if status == 200:
                print(f"{GREEN}✅ {name:15} ({desc}): Running{RESET}")
            else:
                print(f"{RED}❌ {name:15} ({desc}): Unexpected status {status}{RESET}")
                all_healthy = False
        except Exception as e:
            print(f"{RED}❌ {name:15} ({desc}): Not accessible{RESET}")
            print(f"   Error: {e}")
            all_healthy = False

    if not all_healthy:
        print(f"\n{YELLOW}⚠️  Warning: Some services are not running{RESET}")
        print(f"{YELLOW}   Please start all services before running tests{RESET}")
        print(f"{YELLOW}   See WEB_SEARCH_TESTING_GUIDE.md for instructions{RESET}")
        return False

    print(f"\n{GREEN}✅ All services are healthy!{RESET}")
    return True


def main():
    """Run all web search tests"""
    start_time = datetime.now()

    print_header("WEB SEARCH FEATURE - COMPLETE TEST SUITE")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Check services first
    if not check_services():
        print(f"\n{RED}Cannot proceed: Services not ready{RESET}")
        return 1

    # Define all tests
    tests = [
        {
            "file": "test_search_service.py",
            "name": "Search Service (Foundation)",
            "phase": "PHASE 1",
            "description": "SearXNG HTTP client"
        },
        {
            "file": "test_web_search_tool.py",
            "name": "Web Search Tool (LangChain)",
            "phase": "PHASE 2",
            "description": "LangChain tool interface"
        },
        {
            "file": "test_agent_web_search_integration.py",
            "name": "Agent Integration",
            "phase": "PHASE 3",
            "description": "Tool added to agent"
        },
        {
            "file": "test_agent_web_search.py",
            "name": "Agent Web Search Usage",
            "phase": "PHASE 4",
            "description": "Agent actively uses web search"
        },
        {
            "file": "test_vision_web_e2e.py",
            "name": "Vision + Web Search E2E",
            "phase": "PHASE 5",
            "description": "Complete integration flow"
        }
    ]

    # Run all tests
    results = []
    for test in tests:
        test_path = os.path.join(os.path.dirname(__file__), test["file"])

        if not os.path.exists(test_path):
            print(f"{RED}❌ Test file not found: {test['file']}{RESET}")
            results.append(False)
            continue

        success = run_test(test_path, test["name"], test["phase"])
        results.append(success)

    # Print summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print_header("TEST SUITE SUMMARY")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Detailed results
    passed = sum(results)
    total = len(results)

    print(f"{BOLD}Test Results:{RESET}")
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"  {i}. [{test['phase']}] {test['name']:30} {status}")
        print(f"     {test['description']}")

    # Overall status
    print(f"\n{BOLD}Overall: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print(f"\n{GREEN}{BOLD}🎉 SUCCESS! All tests passed!{RESET}")
        print(f"\n{GREEN}The web search feature is fully functional:{RESET}")
        print(f"{GREEN}  ✓ Search service (SearXNG) working{RESET}")
        print(f"{GREEN}  ✓ LangChain tool integration working{RESET}")
        print(f"{GREEN}  ✓ Agent has web search capability{RESET}")
        print(f"{GREEN}  ✓ Agent actively uses web search{RESET}")
        print(f"{GREEN}  ✓ Vision + web search integration working{RESET}")
        print(f"\n{GREEN}You can now:{RESET}")
        print(f"{GREEN}  • Ask the agent factual questions{RESET}")
        print(f"{GREEN}  • Get current/real-time information{RESET}")
        print(f"{GREEN}  • Detect objects in images{RESET}")
        print(f"{GREEN}  • Ask about detected objects{RESET}")
        print(f"{GREEN}  • Search for information about detected objects{RESET}")
        return 0

    elif passed >= total // 2:
        print(f"\n{YELLOW}⚠️  PARTIAL SUCCESS{RESET}")
        print(f"{YELLOW}Most tests passed, but some issues remain.{RESET}")
        return 1

    else:
        print(f"\n{RED}❌ FAILURE{RESET}")
        print(f"{RED}Multiple tests failed. Check the output above for details.{RESET}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test suite interrupted by user{RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}Test suite crashed: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
