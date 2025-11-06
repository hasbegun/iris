#!/usr/bin/env python3
"""
Test script for ReAct Agent with Vision Analysis and YOLO Detection
"""
import asyncio
import aiohttp
import sys
from pathlib import Path


BASE_URL = "http://localhost:9000"


async def upload_image(image_path: str) -> tuple[str, str]:
    """Upload an image and create a session"""
    async with aiohttp.ClientSession() as session:
        with open(image_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('image', f, filename='test.jpg', content_type='image/jpeg')
            data.add_field('prompt', 'Initial upload')

            async with session.post(f"{BASE_URL}/api/vision/analyze", data=data) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    raise Exception(f"Failed to upload image: {error}")

                result = await resp.json()
                return result['session_id'], result['response']


async def test_agent_query(session_id: str, query: str) -> dict:
    """Test the agent with a specific query"""
    async with aiohttp.ClientSession() as session:
        data = {
            "query": query,
            "session_id": session_id
        }

        async with session.post(f"{BASE_URL}/api/agent/query", json=data) as resp:
            if resp.status != 200:
                error = await resp.text()
                raise Exception(f"Agent query failed: {error}")

            return await resp.json()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_react_agent.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    if not Path(image_path).exists():
        print(f"Error: Image not found: {image_path}")
        sys.exit(1)

    print(f"\n{'='*80}")
    print(f"Testing ReAct Agent with Vision Analysis + YOLO Detection")
    print(f"{'='*80}\n")

    print(f"📸 Uploading image: {image_path}")
    session_id, initial_response = await upload_image(image_path)
    print(f"✅ Session created: {session_id}")
    print(f"   Initial analysis: {initial_response[:100]}...\n")

    # Test queries
    test_queries = [
        {
            "name": "General Description (should use vision_analysis)",
            "query": "What's in this image?"
        },
        {
            "name": "Specific Object Detection (should use detect_objects)",
            "query": "Find all people in this image"
        },
        {
            "name": "Object Counting (should use detect_objects)",
            "query": "How many cars are there?"
        },
        {
            "name": "Complex Query (may use multiple tools)",
            "query": "Describe what you see and tell me how many people are present"
        }
    ]

    for i, test in enumerate(test_queries, 1):
        print(f"\n{'─'*80}")
        print(f"Test {i}/{len(test_queries)}: {test['name']}")
        print(f"{'─'*80}")
        print(f"Query: {test['query']}")
        print(f"\nProcessing...")

        try:
            result = await test_agent_query(session_id, test['query'])

            if result['status'] == 'success':
                print(f"\n✅ Agent Response:")
                print(f"{result['response']}\n")
            else:
                print(f"\n❌ Error: {result.get('response', 'Unknown error')}\n")

        except Exception as e:
            print(f"\n❌ Exception: {str(e)}\n")

    print(f"\n{'='*80}")
    print(f"Testing Complete!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
