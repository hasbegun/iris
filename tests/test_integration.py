#!/usr/bin/env python3
"""
Integration Test Script for YOLO ML Service
Tests the complete flow: ML Service -> Backend -> Agent
"""
import sys
import time
import requests
from pathlib import Path
import json

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text):
    """Print formatted header"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text.center(60)}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_info(text):
    """Print info message"""
    print(f"  {text}")


class IntegrationTester:
    """Integration test runner"""

    def __init__(self):
        self.ml_service_url = "http://localhost:9001"
        self.backend_url = "http://localhost:9000"
        self.test_image_path = None
        self.session_id = None

    def check_service_health(self, service_name, url):
        """Check if a service is healthy"""
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            print_success(f"{service_name} is running at {url}")
            return True
        except requests.exceptions.ConnectionError:
            print_error(f"{service_name} is not running at {url}")
            print_info(f"Please start {service_name} first")
            return False
        except Exception as e:
            print_error(f"{service_name} health check failed: {e}")
            return False

    def test_ml_service_health(self):
        """Test ML service health endpoint"""
        print_header("Testing ML Service Health")

        if not self.check_service_health("ML Service", f"{self.ml_service_url}/health"):
            return False

        try:
            response = requests.get(f"{self.ml_service_url}/health")
            health = response.json()

            print_info(f"Status: {health.get('status')}")
            print_info(f"Models loaded: {health.get('models_loaded')}")
            print_info(f"Device: {health.get('device')}")

            if health.get('status') == 'healthy' and health.get('models_loaded'):
                print_success("ML Service is fully operational")
                return True
            else:
                print_warning("ML Service is running but models may not be loaded yet")
                print_info("This is normal on first startup - models are loading...")
                return True

        except Exception as e:
            print_error(f"Failed to get ML service health: {e}")
            return False

    def test_backend_health(self):
        """Test backend health endpoint"""
        print_header("Testing Backend Health")

        if not self.check_service_health("Backend", f"{self.backend_url}/api/health"):
            return False

        try:
            response = requests.get(f"{self.backend_url}/api/health")
            health = response.json()

            print_info(f"Status: {health.get('status')}")
            print_info(f"Ollama connected: {health.get('ollama_connected')}")
            print_info(f"Available models: {len(health.get('available_models', []))}")

            print_success("Backend is operational")
            return True

        except Exception as e:
            print_error(f"Failed to get backend health: {e}")
            return False

    def test_agent_health(self):
        """Test agent service health"""
        print_header("Testing Agent Service Health")

        try:
            response = requests.get(f"{self.backend_url}/api/agent/health")
            health = response.json()

            print_info(f"Status: {health.get('status')}")

            agent_info = health.get('agent', {})
            print_info(f"Agent initialized: {agent_info.get('initialized')}")
            print_info(f"LLM model: {agent_info.get('model')}")
            print_info(f"Tools available: {agent_info.get('tools_count')}")

            ml_info = health.get('ml_service', {})
            print_info(f"ML Service connected: {ml_info.get('status') == 'healthy'}")

            if health.get('status') == 'healthy':
                print_success("Agent service is fully operational")
                return True
            else:
                print_warning("Agent service has issues")
                return False

        except Exception as e:
            print_error(f"Failed to get agent health: {e}")
            return False

    def find_test_image(self):
        """Find a test image to use"""
        print_header("Locating Test Image")

        # Check common locations
        possible_paths = [
            "test-imgs/sample.jpg",
            "test-imgs/test.jpg",
            "../test-imgs/sample.jpg",
        ]

        for path_str in possible_paths:
            path = Path(path_str)
            if path.exists():
                self.test_image_path = str(path)
                print_success(f"Found test image: {self.test_image_path}")
                return True

        print_warning("No test image found")
        print_info("Please provide path to a test image")
        print_info("Usage: python test_integration.py <path_to_image>")

        # Check if user provided image path
        if len(sys.argv) > 1:
            path = Path(sys.argv[1])
            if path.exists():
                self.test_image_path = str(path)
                print_success(f"Using provided image: {self.test_image_path}")
                return True
            else:
                print_error(f"Image not found: {sys.argv[1]}")
                return False

        return False

    def test_ml_service_detection(self):
        """Test ML service object detection"""
        print_header("Testing ML Service - Object Detection")

        if not self.test_image_path:
            print_warning("Skipping - no test image available")
            return True

        try:
            with open(self.test_image_path, 'rb') as f:
                files = {'image': f}
                data = {'confidence': 0.5}

                response = requests.post(
                    f"{self.ml_service_url}/api/detect",
                    files=files,
                    data=data,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()

            print_info(f"Detected {result.get('count', 0)} objects")
            print_info(f"Inference time: {result.get('inference_time_ms', 0):.2f}ms")

            if result.get('detections'):
                print_info("Objects found:")
                for det in result['detections'][:5]:
                    print_info(f"  - {det['class_name']}: {det['confidence']:.2f}")

            print_success("ML Service detection working")
            return True

        except Exception as e:
            print_error(f"ML Service detection failed: {e}")
            return False

    def upload_image_to_backend(self):
        """Upload image to backend to get session"""
        print_header("Uploading Image to Backend")

        if not self.test_image_path:
            print_warning("Skipping - no test image available")
            return True

        try:
            with open(self.test_image_path, 'rb') as f:
                files = {'image': f}
                data = {'prompt': 'Describe this image'}

                response = requests.post(
                    f"{self.backend_url}/api/vision/analyze",
                    files=files,
                    data=data,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()

            self.session_id = result.get('session_id')
            print_success(f"Image uploaded, session ID: {self.session_id}")
            print_info(f"Vision analysis: {result.get('response', '')[:100]}...")

            return True

        except Exception as e:
            print_error(f"Failed to upload image: {e}")
            return False

    def test_agent_query(self, query):
        """Test agent query"""
        if not self.session_id:
            print_warning("Skipping - no session available")
            return True

        try:
            response = requests.post(
                f"{self.backend_url}/api/agent/query",
                json={
                    'query': query,
                    'session_id': self.session_id
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()

            print_info(f"Query: {query}")
            print_info(f"Response: {result.get('response', '')}")
            print_success("Agent query successful")

            return True

        except Exception as e:
            print_error(f"Agent query failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print_info(f"Error details: {e.response.text}")
            return False

    def test_agent_queries(self):
        """Test multiple agent queries"""
        print_header("Testing Agent Queries")

        queries = [
            "How many objects do you see?",
            "What vehicles are in this image?",
            "Are there any people?",
        ]

        success_count = 0
        for query in queries:
            print()
            if self.test_agent_query(query):
                success_count += 1
            time.sleep(1)  # Small delay between queries

        print()
        print_info(f"Completed {success_count}/{len(queries)} queries successfully")
        return success_count > 0

    def test_direct_detection(self):
        """Test direct detection endpoint"""
        print_header("Testing Direct Detection")

        if not self.session_id:
            print_warning("Skipping - no session available")
            return True

        try:
            response = requests.post(
                f"{self.backend_url}/api/agent/detect",
                json={
                    'session_id': self.session_id,
                    'object_types': 'car,person,dog,cat',
                    'confidence': 0.5
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            print_info(f"Status: {result.get('status')}")
            print_info(f"Found {result.get('total_count', 0)} objects")
            print_info(f"Summary: {result.get('summary', '')}")

            print_success("Direct detection working")
            return True

        except Exception as e:
            print_error(f"Direct detection failed: {e}")
            return False

    def run_all_tests(self):
        """Run all integration tests"""
        print_header("YOLO ML Service Integration Tests")
        print_info(f"ML Service: {self.ml_service_url}")
        print_info(f"Backend: {self.backend_url}")

        tests = [
            ("ML Service Health", self.test_ml_service_health),
            ("Backend Health", self.test_backend_health),
            ("Agent Health", self.test_agent_health),
            ("Find Test Image", self.find_test_image),
            ("ML Service Detection", self.test_ml_service_detection),
            ("Upload Image", self.upload_image_to_backend),
            ("Agent Queries", self.test_agent_queries),
            ("Direct Detection", self.test_direct_detection),
        ]

        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))

                if not result and test_name in ["ML Service Health", "Backend Health"]:
                    print_error("Critical service is down. Stopping tests.")
                    break

            except Exception as e:
                print_error(f"Test '{test_name}' crashed: {e}")
                results.append((test_name, False))

        # Print summary
        print_header("Test Summary")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            if result:
                print_success(f"{test_name}")
            else:
                print_error(f"{test_name}")

        print()
        if passed == total:
            print_success(f"All tests passed! ({passed}/{total})")
        else:
            print_warning(f"Some tests failed ({passed}/{total})")

        return passed == total


def main():
    """Main entry point"""
    tester = IntegrationTester()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
