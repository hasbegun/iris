"""
YOLO Service for object detection, segmentation, and face detection
Handles model loading, inference, and result parsing
"""
import asyncio
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict
import io
from PIL import Image

from app.config import settings
from app.models.schemas import Detection, Segment
from app.utils.image_utils import bytes_to_image, resize_image, validate_image

# Lazy import to avoid issues if torch/ultralytics not installed
try:
    from ultralytics import YOLO
    import torch
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    logging.warning("Ultralytics not installed. ML features will be disabled.")

logger = logging.getLogger(__name__)


class YOLOService:
    """
    YOLO inference service
    Manages model loading and inference for detection, segmentation, and face detection
    """

    def __init__(self):
        """Initialize YOLO service"""
        if not ULTRALYTICS_AVAILABLE:
            raise ImportError(
                "Ultralytics YOLO is not installed. "
                "Please install it with: pip install ultralytics torch torchvision"
            )

        self.detection_model: Optional[YOLO] = None
        self.segmentation_model: Optional[YOLO] = None
        self.face_model: Optional[YOLO] = None

        # Thread pool for CPU/GPU-bound operations
        self.executor = ThreadPoolExecutor(max_workers=settings.num_workers)

        # Device configuration
        self.device = self._get_device()

        # Metrics
        self.total_requests = 0
        self.total_inference_time = 0.0
        self.models_loaded = False
        self.start_time = time.time()

        logger.info(f"YOLOService initialized on device: {self.device}")

    def _get_device(self) -> str:
        """
        Determine the device to use for inference

        Returns:
            Device string ("cuda", "mps", or "cpu")
        """
        if settings.device == "cuda" and torch.cuda.is_available():
            logger.info(f"NVIDIA GPU available: {torch.cuda.get_device_name(0)}")
            return "cuda"
        elif settings.device == "cuda":
            logger.warning("CUDA requested but not available. Using CPU.")
            return "cpu"
        elif settings.device == "mps" and torch.backends.mps.is_available():
            logger.info("Apple Silicon GPU (MPS) available")
            return "mps"
        elif settings.device == "mps":
            logger.warning("MPS requested but not available. Using CPU.")
            return "cpu"
        else:
            return "cpu"

    async def load_models(self):
        """
        Load all YOLO models on startup
        Run in thread pool to avoid blocking
        """
        logger.info("Loading YOLO models...")
        loop = asyncio.get_event_loop()

        try:
            # Load detection model
            logger.info(f"Loading detection model: {settings.detection_model_path}")
            self.detection_model = await loop.run_in_executor(
                self.executor,
                lambda: YOLO(settings.detection_model_path)
            )
            self.detection_model.to(self.device)

            # Load segmentation model
            logger.info(f"Loading segmentation model: {settings.segmentation_model_path}")
            self.segmentation_model = await loop.run_in_executor(
                self.executor,
                lambda: YOLO(settings.segmentation_model_path)
            )
            self.segmentation_model.to(self.device)

            # Load face detection model (use detection model if face model not available)
            try:
                logger.info(f"Loading face detection model: {settings.face_model_path}")
                self.face_model = await loop.run_in_executor(
                    self.executor,
                    lambda: YOLO(settings.face_model_path)
                )
                self.face_model.to(self.device)
            except Exception as e:
                logger.warning(f"Face model not available, using detection model for person detection: {e}")
                self.face_model = self.detection_model

            # Warmup models if configured
            if settings.model_warmup:
                await self._warmup_models()

            self.models_loaded = True
            logger.info("✅ All YOLO models loaded successfully")

        except Exception as e:
            logger.error(f"❌ Failed to load models: {e}")
            raise

    async def _warmup_models(self):
        """
        Warmup models with dummy inference
        Improves first real inference speed
        """
        logger.info("Warming up models...")
        loop = asyncio.get_event_loop()

        # Create dummy image (640x640 RGB)
        dummy_image = Image.new('RGB', (640, 640), color='white')

        try:
            # Warmup detection
            await loop.run_in_executor(
                self.executor,
                lambda: self.detection_model.predict(dummy_image, verbose=False)
            )

            # Warmup segmentation
            await loop.run_in_executor(
                self.executor,
                lambda: self.segmentation_model.predict(dummy_image, verbose=False)
            )

            logger.info("✅ Model warmup complete")
        except Exception as e:
            logger.warning(f"Model warmup failed: {e}")

    async def detect(
        self,
        image_bytes: bytes,
        confidence: float = 0.5,
        classes: Optional[List[str]] = None
    ) -> Dict:
        """
        Perform object detection

        Args:
            image_bytes: Image data as bytes
            confidence: Detection confidence threshold (0.0-1.0)
            classes: List of class names to detect (None = all classes)

        Returns:
            Dictionary with detection results
        """
        start_time = time.time()

        # Note: Validation is now handled by handler layer (ImageValidator/VideoValidator)

        # Convert to PIL Image
        try:
            image = bytes_to_image(image_bytes)
        except Exception as e:
            return {"status": "error", "message": f"Unable to process image: {str(e)}"}

        # Resize if needed
        image = resize_image(image, settings.max_image_size)

        # Convert class names to class IDs if specified
        class_ids = self._get_class_ids(classes) if classes else None

        # Run inference in thread pool
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            self.executor,
            lambda: self.detection_model.predict(
                image,
                conf=confidence,
                classes=class_ids,
                verbose=False
            )
        )

        # Parse results
        detections = self._parse_detection_results(results[0])

        # Calculate inference time
        inference_time = (time.time() - start_time) * 1000  # Convert to ms

        # Update metrics
        self.total_requests += 1
        self.total_inference_time += inference_time

        return {
            "status": "success",
            "detections": detections,
            "count": len(detections),
            "image_shape": results[0].orig_shape,
            "inference_time_ms": round(inference_time, 2)
        }

    async def segment(
        self,
        image_bytes: bytes,
        confidence: float = 0.5,
        classes: Optional[List[str]] = None
    ) -> Dict:
        """
        Perform instance segmentation

        Args:
            image_bytes: Image data as bytes
            confidence: Segmentation confidence threshold (0.0-1.0)
            classes: List of class names to segment (None = all classes)

        Returns:
            Dictionary with segmentation results
        """
        start_time = time.time()

        # Note: Validation is now handled by handler layer (ImageValidator/VideoValidator)

        # Convert to PIL Image
        try:
            image = bytes_to_image(image_bytes)
        except Exception as e:
            return {"status": "error", "message": f"Unable to process image: {str(e)}"}

        # Resize if needed
        image = resize_image(image, settings.max_image_size)

        # Convert class names to class IDs if specified
        class_ids = self._get_class_ids(classes) if classes else None

        # Run inference
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            self.executor,
            lambda: self.segmentation_model.predict(
                image,
                conf=confidence,
                classes=class_ids,
                verbose=False
            )
        )

        # Parse results
        segments = self._parse_segmentation_results(results[0])

        # Calculate inference time
        inference_time = (time.time() - start_time) * 1000

        # Update metrics
        self.total_requests += 1
        self.total_inference_time += inference_time

        return {
            "status": "success",
            "segments": segments,
            "count": len(segments),
            "image_shape": results[0].orig_shape,
            "inference_time_ms": round(inference_time, 2)
        }

    async def detect_faces(
        self,
        image_bytes: bytes,
        confidence: float = 0.5
    ) -> Dict:
        """
        Detect human faces

        Args:
            image_bytes: Image data as bytes
            confidence: Detection confidence threshold (0.0-1.0)

        Returns:
            Dictionary with face detection results
        """
        start_time = time.time()

        # Note: Validation is now handled by handler layer (ImageValidator/VideoValidator)

        # Convert to PIL Image
        try:
            image = bytes_to_image(image_bytes)
        except Exception as e:
            return {"status": "error", "message": f"Unable to process image: {str(e)}"}

        # Resize if needed
        image = resize_image(image, settings.max_image_size)

        # If using dedicated face model, use it; otherwise filter for 'person' class
        loop = asyncio.get_event_loop()

        if self.face_model != self.detection_model:
            # Dedicated face model
            results = await loop.run_in_executor(
                self.executor,
                lambda: self.face_model.predict(
                    image,
                    conf=confidence,
                    verbose=False
                )
            )
        else:
            # Use detection model filtered to 'person' class (class ID 0 in COCO)
            results = await loop.run_in_executor(
                self.executor,
                lambda: self.detection_model.predict(
                    image,
                    conf=confidence,
                    classes=[0],  # person class
                    verbose=False
                )
            )

        # Parse results
        faces = self._parse_detection_results(results[0])

        # Calculate inference time
        inference_time = (time.time() - start_time) * 1000

        # Update metrics
        self.total_requests += 1
        self.total_inference_time += inference_time

        return {
            "status": "success",
            "faces": faces,
            "count": len(faces),
            "image_shape": results[0].orig_shape,
            "inference_time_ms": round(inference_time, 2)
        }

    def _parse_detection_results(self, result) -> List[Dict]:
        """
        Parse YOLO detection results into structured format

        Args:
            result: YOLO result object

        Returns:
            List of detection dictionaries
        """
        detections = []

        if result.boxes is None or len(result.boxes) == 0:
            return detections

        for box in result.boxes:
            detections.append({
                "class_name": result.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            })

        return detections

    def _parse_segmentation_results(self, result) -> List[Dict]:
        """
        Parse YOLO segmentation results into structured format

        Args:
            result: YOLO result object

        Returns:
            List of segmentation dictionaries
        """
        segments = []

        if result.masks is None or len(result.masks) == 0:
            return segments

        for i, mask in enumerate(result.masks):
            segments.append({
                "class_name": result.names[int(result.boxes[i].cls)],
                "confidence": float(result.boxes[i].conf),
                "bbox": result.boxes[i].xyxy[0].tolist(),
                "mask": mask.xy[0].tolist()  # Polygon points
            })

        return segments

    def _get_class_ids(self, class_names: List[str]) -> Optional[List[int]]:
        """
        Convert class names to class IDs

        Args:
            class_names: List of class names

        Returns:
            List of class IDs, or None if no valid classes found
        """
        if not class_names or not self.detection_model:
            return None

        class_ids = []
        model_names = self.detection_model.names  # Dict: {id: name}

        # Reverse lookup: name -> id
        name_to_id = {v.lower(): k for k, v in model_names.items()}

        for name in class_names:
            # Clean up class name (remove quotes, extra spaces)
            name_clean = name.strip().strip('"').strip("'").strip().lower()
            if name_clean in name_to_id:
                class_ids.append(name_to_id[name_clean])
            # Silently skip invalid classes - YOLO will just detect all objects

        # If no valid classes found, return None to detect all objects
        return class_ids if class_ids else None

    def get_avg_inference_time(self) -> float:
        """
        Get average inference time in milliseconds

        Returns:
            Average inference time
        """
        if self.total_requests == 0:
            return 0.0
        return round(self.total_inference_time / self.total_requests, 2)

    def get_memory_usage(self) -> float:
        """
        Get current memory usage in MB

        Returns:
            Memory usage in MB
        """
        if self.device == "cuda" and torch.cuda.is_available():
            return round(torch.cuda.memory_allocated() / (1024 ** 2), 2)
        else:
            # For CPU, approximate based on loaded models
            import psutil
            process = psutil.Process()
            return round(process.memory_info().rss / (1024 ** 2), 2)

    def get_uptime(self) -> float:
        """
        Get service uptime in seconds

        Returns:
            Uptime in seconds
        """
        return round(time.time() - self.start_time, 2)
