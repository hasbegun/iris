"""
Query Classification and Object Extraction Utilities

Helps classify user voice queries and extract mentioned objects
for hallucination prevention.
"""
import re
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

# Common object nouns that YOLO can detect
YOLO_DETECTABLE_OBJECTS = [
    "person", "people", "human", "man", "woman", "child", "baby",
    "bicycle", "bike", "car", "motorcycle", "motorbike", "airplane", "plane",
    "bus", "train", "truck", "boat", "ship",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear",
    "zebra", "giraffe", "backpack", "umbrella", "handbag", "bag", "tie",
    "suitcase", "frisbee", "skis", "snowboard", "sports ball", "ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket", "bottle", "wine glass", "cup", "fork", "knife",
    "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
    "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "plant", "bed", "dining table", "table", "toilet",
    "tv", "television", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book",
    "clock", "vase", "scissors", "teddy bear", "toy", "hair drier", "toothbrush"
]

# Dangerous objects for safety queries
DANGEROUS_OBJECTS = [
    "knife", "scissors", "fire", "flame", "gun", "weapon", "sharp",
    "needle", "broken glass", "chemical", "poison", "hazard"
]


class QueryType:
    """Query type constants"""
    OBJECT_IDENTIFICATION = "object"
    ACTION_RECOGNITION = "action"
    SAFETY_CHECK = "safety"
    COUNTING = "count"
    GENERAL_DESCRIPTION = "general"


def classify_query(query: str) -> str:
    """
    Classify the type of voice query.

    Args:
        query: User's voice query text

    Returns:
        Query type constant (object, action, safety, count, general)
    """
    query_lower = query.lower().strip()

    # Safety check queries
    if any(word in query_lower for word in ["dangerous", "danger", "safe", "unsafe", "risk", "hazard"]):
        return QueryType.SAFETY_CHECK

    # Counting queries
    if any(phrase in query_lower for phrase in ["how many", "count", "number of"]):
        return QueryType.COUNTING

    # Action recognition queries
    if any(word in query_lower for word in ["doing", "action", "activity", "performing", "happening"]):
        return QueryType.ACTION_RECOGNITION

    # Object identification queries
    if any(phrase in query_lower for phrase in [
        "what is this", "what's this", "what is that", "what's that",
        "describe this", "describe that", "tell me about this", "tell me about that",
        "identify", "recognize"
    ]):
        return QueryType.OBJECT_IDENTIFICATION

    # General description (fallback)
    return QueryType.GENERAL_DESCRIPTION


def extract_objects_from_query(query: str) -> List[str]:
    """
    Extract object nouns mentioned in the query.

    Args:
        query: User's voice query text

    Returns:
        List of detected object names mentioned in query
    """
    query_lower = query.lower()
    mentioned_objects = []

    # Check for each detectable object
    for obj in YOLO_DETECTABLE_OBJECTS:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(obj) + r'\b'
        if re.search(pattern, query_lower):
            mentioned_objects.append(obj)

    logger.info(f"Extracted objects from query: {mentioned_objects}")
    return mentioned_objects


def extract_dangerous_objects_from_query(query: str) -> List[str]:
    """
    Extract dangerous object keywords from query.

    Args:
        query: User's voice query text

    Returns:
        List of dangerous object keywords mentioned
    """
    query_lower = query.lower()
    mentioned_dangerous = []

    for obj in DANGEROUS_OBJECTS:
        pattern = r'\b' + re.escape(obj) + r'\b'
        if re.search(pattern, query_lower):
            mentioned_dangerous.append(obj)

    return mentioned_dangerous


def verify_object_in_detections(
    mentioned_objects: List[str],
    detected_objects: List[dict]
) -> Tuple[bool, List[str]]:
    """
    Verify if mentioned objects exist in YOLO detections.

    Args:
        mentioned_objects: List of objects mentioned in query
        detected_objects: List of YOLO detection dictionaries with 'class_name'

    Returns:
        Tuple of (all_found: bool, missing_objects: List[str])
    """
    if not mentioned_objects:
        return True, []

    # Extract detected class names
    detected_classes = [det.get('class_name', '').lower() for det in detected_objects]

    missing_objects = []
    for obj in mentioned_objects:
        obj_lower = obj.lower()

        # Check if object or similar term is in detections
        # Handle plurals and variations
        found = False
        for detected in detected_classes:
            if obj_lower in detected or detected in obj_lower:
                found = True
                break
            # Handle common variations
            if obj_lower == "people" and detected == "person":
                found = True
                break
            if obj_lower == "bike" and detected == "bicycle":
                found = True
                break
            if obj_lower == "car" and detected in ["car", "truck", "bus"]:
                found = True
                break

        if not found:
            missing_objects.append(obj)

    all_found = len(missing_objects) == 0
    return all_found, missing_objects


def should_verify_with_detection(query_type: str) -> bool:
    """
    Determine if a query should use YOLO detection for verification.

    Args:
        query_type: The classified query type

    Returns:
        True if YOLO verification should be used
    """
    # Safety checks always need verification
    if query_type == QueryType.SAFETY_CHECK:
        return True

    # Object identification needs verification
    if query_type == QueryType.OBJECT_IDENTIFICATION:
        return True

    # Counting always needs detection
    if query_type == QueryType.COUNTING:
        return True

    # Action recognition benefits from verification
    if query_type == QueryType.ACTION_RECOGNITION:
        return True

    # General descriptions might not need it
    return False
