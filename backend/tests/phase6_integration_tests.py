"""
Phase 6: Integration & Testing
Comprehensive integration tests for the Vision AI Backend.
"""
import requests
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple
import statistics

# Configuration
BASE_URL = "http://localhost:8888"
TEST_IMAGES_DIR = Path(__file__).parent.parent.parent / "test-imgs"

# Test images for different scenarios
TEST_SCENARIOS = [
    {
        "name": "Tesla Maintenance Poster",
        "file": "tesla_man.jpg",
        "initial_prompt": "What am I looking at? Describe everything you see.",
        "follow_up_questions": [
            "What are the main maintenance points mentioned?",
            "Is this related to electric vehicles?"
        ]
    },
    {
        "name": "Face Detection - Kid with Balloons",
        "file": "kid1.jpg",
        "initial_prompt": "What do you see in this image?",
        "follow_up_questions": [
            "How many people are in the image?",
            "What activity or event is happening?"
        ]
    },
    {
        "name": "Food - Kimchi Soup",
        "file": "kimchi_soup.jpg",
        "initial_prompt": "What food is this?",
        "follow_up_questions": [
            "What are the main ingredients visible?",
            "What cuisine does this belong to?"
        ]
    },
    {
        "name": "Food - Fried Rice",
        "file": "fried_rice.jpg",
        "initial_prompt": "Describe this dish.",
        "follow_up_questions": [
            "What ingredients can you identify?",
            "How would you prepare this?"
        ]
    }
]


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def check_health() -> bool:
    """Check if the backend is healthy."""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "healthy" and data.get("ollama_connected"):
            print_success(f"Backend is healthy")
            print_info(f"Available models: {len(data.get('available_models', []))}")
            return True
        else:
            print_error("Backend is not healthy")
            return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


def test_vision_analysis(image_file: str, prompt: str) -> Tuple[bool, Dict, float]:
    """Test vision analysis endpoint."""
    image_path = TEST_IMAGES_DIR / image_file

    if not image_path.exists():
        print_error(f"Image not found: {image_path}")
        return False, {}, 0.0

    try:
        start_time = time.time()

        with open(image_path, 'rb') as f:
            files = {'image': (image_file, f, 'image/jpeg')}
            data = {'prompt': prompt}

            response = requests.post(
                f"{BASE_URL}/api/vision/analyze",
                files=files,
                data=data,
                timeout=60
            )

        elapsed_time = time.time() - start_time
        response.raise_for_status()
        result = response.json()

        return True, result, elapsed_time

    except Exception as e:
        print_error(f"Vision analysis failed: {e}")
        return False, {}, 0.0


def test_chat(session_id: str, message: str) -> Tuple[bool, Dict, float]:
    """Test chat endpoint."""
    try:
        start_time = time.time()

        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"session_id": session_id, "message": message},
            headers={"Content-Type": "application/json"},
            timeout=60
        )

        elapsed_time = time.time() - start_time
        response.raise_for_status()
        result = response.json()

        return True, result, elapsed_time

    except Exception as e:
        print_error(f"Chat failed: {e}")
        return False, {}, 0.0


def run_scenario_test(scenario: Dict) -> Dict:
    """Run a complete test scenario with vision analysis and follow-up chat."""
    print_header(f"Test Scenario: {scenario['name']}")

    metrics = {
        "success": True,
        "vision_latency": 0.0,
        "chat_latencies": [],
        "total_time": 0.0
    }

    start_total = time.time()

    # Step 1: Analyze image
    print_info(f"Analyzing image: {scenario['file']}")
    print_info(f"Prompt: {scenario['initial_prompt']}")

    success, result, latency = test_vision_analysis(
        scenario['file'],
        scenario['initial_prompt']
    )

    if not success:
        metrics["success"] = False
        return metrics

    metrics["vision_latency"] = latency
    session_id = result.get("session_id")
    model_used = result.get("model_used")
    response_text = result.get("response", "")

    print_success(f"Vision analysis completed in {latency:.2f}s")
    print_info(f"Session ID: {session_id}")
    print_info(f"Model: {model_used}")
    print(f"\n{Colors.OKBLUE}Response:{Colors.ENDC}")
    print(f"{response_text[:300]}..." if len(response_text) > 300 else response_text)

    # Step 2: Follow-up chat questions
    for i, question in enumerate(scenario['follow_up_questions'], 1):
        print(f"\n{Colors.OKCYAN}Follow-up Question {i}:{Colors.ENDC} {question}")

        success, result, latency = test_chat(session_id, question)

        if not success:
            metrics["success"] = False
            return metrics

        metrics["chat_latencies"].append(latency)
        response_text = result.get("response", "")

        print_success(f"Chat response received in {latency:.2f}s")
        print(f"{Colors.OKBLUE}Response:{Colors.ENDC}")
        print(f"{response_text[:300]}..." if len(response_text) > 300 else response_text)

    metrics["total_time"] = time.time() - start_total

    # Print metrics summary
    print(f"\n{Colors.BOLD}Scenario Metrics:{Colors.ENDC}")
    print(f"  Vision Analysis: {metrics['vision_latency']:.2f}s")
    if metrics["chat_latencies"]:
        avg_chat = statistics.mean(metrics["chat_latencies"])
        print(f"  Average Chat: {avg_chat:.2f}s")
    print(f"  Total Time: {metrics['total_time']:.2f}s")

    return metrics


def run_performance_benchmark():
    """Run performance benchmarks on a single image."""
    print_header("Performance Benchmark")

    # Use the first test image
    test_file = "tesla_man.jpg"
    prompt = "Describe this image briefly."

    print_info(f"Running 5 iterations with {test_file}")

    latencies = []

    for i in range(5):
        print(f"\n{Colors.OKCYAN}Iteration {i + 1}/5{Colors.ENDC}")
        success, result, latency = test_vision_analysis(test_file, prompt)

        if success:
            latencies.append(latency)
            print_success(f"Completed in {latency:.2f}s")
        else:
            print_error(f"Failed at iteration {i + 1}")

    if latencies:
        print(f"\n{Colors.BOLD}Performance Metrics:{Colors.ENDC}")
        print(f"  Mean: {statistics.mean(latencies):.2f}s")
        print(f"  Median: {statistics.median(latencies):.2f}s")
        print(f"  Min: {min(latencies):.2f}s")
        print(f"  Max: {max(latencies):.2f}s")
        print(f"  Std Dev: {statistics.stdev(latencies) if len(latencies) > 1 else 0:.2f}s")


def run_all_tests():
    """Run all integration tests."""
    print_header("Phase 6: Integration & Testing")
    print_info(f"Backend URL: {BASE_URL}")
    print_info(f"Test Images Directory: {TEST_IMAGES_DIR}")

    # Health check
    print("\n")
    if not check_health():
        print_error("Health check failed. Exiting.")
        return

    # Run all scenario tests
    all_metrics = []
    successful_scenarios = 0

    for scenario in TEST_SCENARIOS:
        metrics = run_scenario_test(scenario)
        all_metrics.append(metrics)
        if metrics["success"]:
            successful_scenarios += 1

    # Run performance benchmark
    run_performance_benchmark()

    # Final summary
    print_header("Test Summary")
    print(f"{Colors.BOLD}Scenarios Passed:{Colors.ENDC} {successful_scenarios}/{len(TEST_SCENARIOS)}")

    if all_metrics:
        all_vision_latencies = [m["vision_latency"] for m in all_metrics if m["success"]]
        all_chat_latencies = [lat for m in all_metrics if m["success"] for lat in m["chat_latencies"]]

        if all_vision_latencies:
            print(f"\n{Colors.BOLD}Average Latencies:{Colors.ENDC}")
            print(f"  Vision Analysis: {statistics.mean(all_vision_latencies):.2f}s")

        if all_chat_latencies:
            print(f"  Chat Responses: {statistics.mean(all_chat_latencies):.2f}s")

    if successful_scenarios == len(TEST_SCENARIOS):
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ All tests passed!{Colors.ENDC}")
    else:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠ Some tests failed!{Colors.ENDC}")


if __name__ == "__main__":
    run_all_tests()
