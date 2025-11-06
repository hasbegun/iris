#!/usr/bin/env python3
"""
CLI test tool for the Vision AI backend.
Supports testing with both images and videos.
"""
import argparse
import asyncio
import aiohttp
import sys
from pathlib import Path
import cv2
import tempfile
from typing import Optional
import json


class VisionAIClient:
    """Client for interacting with the Vision AI API."""

    def __init__(self, base_url: str = "http://localhost:9000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None

    async def health_check(self) -> dict:
        """Check if the API is healthy."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/health") as response:
                return await response.json()

    async def analyze_image(self, image_path: Path, prompt: str) -> dict:
        """Analyze a single image."""
        async with aiohttp.ClientSession() as session:
            with open(image_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field("image", f, filename=image_path.name)
                data.add_field("prompt", prompt)
                if self.session_id:
                    data.add_field("session_id", self.session_id)

                async with session.post(
                    f"{self.base_url}/api/vision/analyze",
                    data=data
                ) as response:
                    result = await response.json()
                    if response.status == 200:
                        self.session_id = result.get("session_id")
                    return result

    async def analyze_video(
        self,
        video_path: Path,
        prompt: str,
        frame_interval: float = 1.0,
        max_frames: int = 60
    ) -> list:
        """Analyze a video by extracting and analyzing frames."""
        print(f"\nProcessing video: {video_path}")
        print(f"Frame interval: {frame_interval}s, Max frames: {max_frames}")

        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        print(f"Video info: {fps:.2f} FPS, {total_frames} frames, {duration:.2f}s duration")

        frame_skip = int(fps * frame_interval)
        results = []

        frame_count = 0
        analyzed_count = 0

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Analyze every Nth frame based on interval
                if frame_count % frame_skip == 0 and analyzed_count < max_frames:
                    timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)

                    # Save frame as temporary image
                    frame_path = tmpdir_path / f"frame_{analyzed_count:04d}.jpg"
                    cv2.imwrite(str(frame_path), frame)

                    # Analyze frame
                    print(f"Analyzing frame {analyzed_count + 1}/{max_frames} "
                          f"(video frame {frame_count}, {timestamp_ms / 1000:.2f}s)...", end="")

                    async with aiohttp.ClientSession() as session:
                        with open(frame_path, "rb") as f:
                            data = aiohttp.FormData()
                            data.add_field("frame", f, filename=frame_path.name)
                            data.add_field("prompt", prompt)
                            data.add_field("frame_number", str(frame_count))
                            data.add_field("timestamp_ms", str(timestamp_ms))
                            if self.session_id:
                                data.add_field("session_id", self.session_id)

                            async with session.post(
                                f"{self.base_url}/api/vision/stream",
                                data=data
                            ) as response:
                                result = await response.json()
                                if response.status == 200:
                                    self.session_id = result.get("session_id")
                                    results.append({
                                        "frame_number": frame_count,
                                        "timestamp_s": timestamp_ms / 1000,
                                        "result": result
                                    })
                                    print(" ✓")
                                else:
                                    print(f" ✗ Error: {result}")

                    analyzed_count += 1

                frame_count += 1

        cap.release()
        print(f"\nAnalyzed {analyzed_count} frames from video")
        return results

    async def chat(self, message: str) -> dict:
        """Send a follow-up chat message."""
        if not self.session_id:
            raise ValueError("No active session. Analyze an image or video first.")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json={
                    "message": message,
                    "session_id": self.session_id
                }
            ) as response:
                return await response.json()


async def interactive_mode(client: VisionAIClient):
    """Run interactive chat mode."""
    print("\n" + "=" * 60)
    print("Interactive mode - Ask follow-up questions")
    print("Commands: 'quit' or 'exit' to end, 'new' for new analysis")
    print("=" * 60)

    while True:
        try:
            message = input("\nYou: ").strip()

            if not message:
                continue

            if message.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if message.lower() == "new":
                client.session_id = None
                print("Session cleared. Ready for new analysis.")
                break

            result = await client.chat(message)

            if "response" in result:
                print(f"\nAssistant: {result['response']}")
                print(f"(Model: {result.get('model_used', 'unknown')})")
            else:
                print(f"\nError: {result}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CLI test tool for Vision AI backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with an image
  python cli_test.py image photo.jpg "What objects do you see?"

  # Test with a video
  python cli_test.py video recording.mp4 "Describe what's happening" --interval 2.0

  # Interactive follow-up questions
  python cli_test.py image photo.jpg "What is this?" --interactive

  # Health check
  python cli_test.py health
        """
    )

    parser.add_argument(
        "mode",
        choices=["image", "video", "health"],
        help="Test mode"
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to image or video file"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Prompt/question for the AI"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:9000",
        help="Base URL of the API (default: http://localhost:9000)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Video frame interval in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=60,
        help="Maximum frames to analyze from video (default: 60)"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Enter interactive mode for follow-up questions"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Save results to JSON file"
    )

    args = parser.parse_args()

    # Initialize client
    client = VisionAIClient(args.url)

    try:
        if args.mode == "health":
            print("Checking API health...")
            result = await client.health_check()
            print(json.dumps(result, indent=2))
            return

        # Validate arguments for image/video modes
        if not args.path or not args.prompt:
            parser.error(f"{args.mode} mode requires path and prompt arguments")

        path = Path(args.path)
        if not path.exists():
            print(f"Error: File not found: {path}")
            sys.exit(1)

        result = None

        if args.mode == "image":
            print(f"\nAnalyzing image: {path}")
            print(f"Prompt: {args.prompt}")
            result = await client.analyze_image(path, args.prompt)

            if "response" in result:
                print("\n" + "=" * 60)
                print("Response:")
                print("=" * 60)
                print(result["response"])
                print("\n" + "-" * 60)
                print(f"Session ID: {result.get('session_id')}")
                print(f"Model: {result.get('model_used')}")

        elif args.mode == "video":
            results = await client.analyze_video(
                path,
                args.prompt,
                args.interval,
                args.max_frames
            )
            result = results

            print("\n" + "=" * 60)
            print("Video Analysis Summary:")
            print("=" * 60)
            for i, frame_result in enumerate(results, 1):
                print(f"\n[Frame {i} @ {frame_result['timestamp_s']:.2f}s]")
                print(frame_result["result"]["response"])

        # Save to file if requested
        if args.output and result:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\nResults saved to: {args.output}")

        # Interactive mode
        if args.interactive and client.session_id:
            await interactive_mode(client)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
