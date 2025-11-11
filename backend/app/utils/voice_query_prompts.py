"""
Voice Query Prompt Templates

Creates specialized prompts for different query types with
hallucination prevention built-in.
"""
from typing import List, Optional
from .query_classifier import QueryType


def create_object_identification_prompt(
    query: str,
    detected_objects: List[str],
    mentioned_objects: List[str]
) -> str:
    """
    Create prompt for object identification queries.

    Args:
        query: Original user query
        detected_objects: List of objects detected by YOLO
        mentioned_objects: Objects mentioned in the query

    Returns:
        Specialized prompt for vision LLM
    """
    # If user asks about specific object but it's not detected
    if mentioned_objects and not any(
        obj.lower() in [d.lower() for d in detected_objects]
        for obj in mentioned_objects
    ):
        return None  # Signal that we should respond with "not found"

    detected_str = ", ".join(detected_objects) if detected_objects else "none"

    prompt = f"""You are analyzing an image to answer a user's question.

DETECTED OBJECTS (from YOLO): {detected_str}

USER QUESTION: {query}

CRITICAL INSTRUCTIONS:
1. ONLY describe objects that appear in the DETECTED OBJECTS list above
2. If the user asks about an object NOT in the detected list, you MUST respond: "I don't see a [object] in the current view"
3. Be specific and factual - describe colors, positions, and observable details
4. Do NOT speculate about objects that weren't detected
5. If you're uncertain, say "I'm not certain" rather than guessing

Answer the user's question based ONLY on what was detected:"""

    return prompt


def create_action_recognition_prompt(
    query: str,
    detected_objects: List[str]
) -> str:
    """
    Create prompt for action recognition queries.

    Args:
        query: Original user query
        detected_objects: List of objects detected by YOLO

    Returns:
        Specialized prompt for vision LLM
    """
    detected_str = ", ".join(detected_objects) if detected_objects else "none"

    # Check if person is in detected objects
    has_person = any(obj.lower() in ["person", "people"] for obj in detected_objects)

    if not has_person and "person" in query.lower():
        return None  # Signal that no person is visible

    prompt = f"""You are analyzing an image to understand what actions are happening.

DETECTED OBJECTS (from YOLO): {detected_str}

USER QUESTION: {query}

CRITICAL INSTRUCTIONS:
1. Describe the action or activity based on visual evidence in the image
2. Consider the pose, position, and context of detected objects
3. If you cannot determine a clear action, describe what you observe without speculation
4. Be factual and specific about observable details
5. If no person is visible and the question asks about a person, respond: "I don't see a person in the current view"

Describe what is happening in the image:"""

    return prompt


def create_safety_check_prompt(
    query: str,
    detected_objects: List[str]
) -> str:
    """
    Create prompt for safety/danger detection queries.

    Args:
        query: Original user query
        detected_objects: List of objects detected by YOLO

    Returns:
        Specialized prompt for vision LLM
    """
    detected_str = ", ".join(detected_objects) if detected_objects else "none"

    # List of potentially dangerous objects
    dangerous_keywords = [
        "knife", "scissors", "fire", "flame", "sharp", "broken glass",
        "weapon", "gun", "tool"
    ]

    detected_dangerous = [
        obj for obj in detected_objects
        if any(keyword in obj.lower() for keyword in dangerous_keywords)
    ]

    prompt = f"""You are analyzing an image for safety concerns.

DETECTED OBJECTS (from YOLO): {detected_str}

USER QUESTION: {query}

CRITICAL INSTRUCTIONS:
1. Identify any potentially dangerous objects from the detected list
2. Look for: sharp objects (knife, scissors), fire, weapons, hazardous items, unsafe conditions
3. Be CONSERVATIVE - if something could be dangerous, mention it
4. ONLY mention dangers that are visible in the detected objects or clearly observable
5. If NO dangerous objects are visible, respond: "I don't see any dangerous objects in the current view"
6. Do NOT speculate about dangers that aren't visible

Potentially dangerous detected: {', '.join(detected_dangerous) if detected_dangerous else 'none'}

Analyze the image for safety concerns:"""

    return prompt


def create_counting_prompt(
    query: str,
    detected_objects: List[str],
    detections: List[dict]
) -> str:
    """
    Create prompt for counting queries.

    Args:
        query: Original user query
        detected_objects: List of unique objects detected
        detections: Full detection list with counts

    Returns:
        Specialized prompt for vision LLM
    """
    # Count objects by class
    class_counts = {}
    for det in detections:
        class_name = det.get('class_name', '')
        class_counts[class_name] = class_counts.get(class_name, 0) + 1

    counts_str = ", ".join([f"{count} {name}(s)" for name, count in class_counts.items()])

    prompt = f"""You are analyzing an image to count objects.

DETECTED OBJECTS WITH COUNTS: {counts_str}

USER QUESTION: {query}

CRITICAL INSTRUCTIONS:
1. Use the EXACT counts from the detection data above
2. If the user asks about an object that wasn't detected, respond: "I don't see any [object] in the current view"
3. Be precise with numbers - use the detection counts, not estimates
4. If asked about multiple objects, list each count

Answer the counting question using the detection data:"""

    return prompt


def create_general_description_prompt(
    query: str,
    detected_objects: Optional[List[str]] = None
) -> str:
    """
    Create prompt for general description queries.

    Args:
        query: Original user query
        detected_objects: Optional list of detected objects for grounding

    Returns:
        Specialized prompt for vision LLM
    """
    if detected_objects:
        detected_str = ", ".join(detected_objects)
        context = f"\n\nDETECTED OBJECTS (for reference): {detected_str}"
    else:
        context = ""

    prompt = f"""You are analyzing an image to provide a description.

USER QUESTION: {query}{context}

INSTRUCTIONS:
1. Provide a clear, factual description of what you see
2. Be specific about colors, positions, and notable details
3. If you're uncertain about something, say so
4. Focus on observable facts rather than speculation

Describe the image:"""

    return prompt


def create_prompt(
    query: str,
    query_type: str,
    detected_objects: List[str],
    detections: List[dict]
) -> Optional[str]:
    """
    Create appropriate prompt based on query type.

    Args:
        query: User's original query
        query_type: Classified query type
        detected_objects: List of unique detected object names
        detections: Full list of detection dictionaries

    Returns:
        Formatted prompt for vision LLM, or None if object not found
    """
    # Extract mentioned objects for verification
    from .query_classifier import extract_objects_from_query

    mentioned_objects = extract_objects_from_query(query)

    if query_type == QueryType.OBJECT_IDENTIFICATION:
        return create_object_identification_prompt(query, detected_objects, mentioned_objects)

    elif query_type == QueryType.ACTION_RECOGNITION:
        return create_action_recognition_prompt(query, detected_objects)

    elif query_type == QueryType.SAFETY_CHECK:
        return create_safety_check_prompt(query, detected_objects)

    elif query_type == QueryType.COUNTING:
        return create_counting_prompt(query, detected_objects, detections)

    elif query_type == QueryType.GENERAL_DESCRIPTION:
        return create_general_description_prompt(query, detected_objects)

    else:
        # Fallback to general
        return create_general_description_prompt(query, detected_objects)


def create_not_found_response(mentioned_objects: List[str]) -> str:
    """
    Create response when mentioned objects are not detected.

    Args:
        mentioned_objects: Objects mentioned but not found

    Returns:
        Natural response indicating object not found
    """
    if len(mentioned_objects) == 1:
        return f"I don't see a {mentioned_objects[0]} in the current view."
    elif len(mentioned_objects) == 2:
        return f"I don't see a {mentioned_objects[0]} or {mentioned_objects[1]} in the current view."
    else:
        objects_str = ", ".join(mentioned_objects[:-1]) + f", or {mentioned_objects[-1]}"
        return f"I don't see a {objects_str} in the current view."
