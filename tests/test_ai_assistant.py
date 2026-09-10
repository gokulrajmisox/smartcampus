import pytest
from src.ai_assistant import GeminiAssistant, normalize_location_name, get_string_similarity

def test_normalization():
    """Test character normalization filters out unwanted symbols."""
    assert normalize_location_name("Acad-1!") == "acad1"
    assert normalize_location_name("Library Block #2") == "libraryblock2"

def test_similarity_bounds():
    """Test string similarity returns ratios between 0.0 and 1.0."""
    sim = get_string_similarity("Library", "Lib")
    assert 0.0 <= sim <= 1.0

def test_fuzzy_matching():
    """Test location matches map successfully to exact POI keys."""
    # Initialize offline assistant
    assistant = GeminiAssistant(api_key="")
    
    assert assistant._find_best_matching_location("library") == "Library"
    assert assistant._find_best_matching_location("acad 1") == "Acad 1"
    assert assistant._find_best_matching_location("hostel") == "Hostel Block"
    assert assistant._find_best_matching_location("entrance") == "Entry gate"

def test_offline_response_navigation():
    """Test navigation parsing in fallback offline mode."""
    assistant = GeminiAssistant(api_key="")
    query = "how to get from library to food court?"
    
    response, context = assistant.get_response(query)
    
    assert response["show_route"] is True
    assert response["start"] == "Library"
    assert response["end"] == "Food Court"
    assert response["query_understood"] is True
    assert "Library" in response["locations"]
    assert "Food Court" in response["locations"]

def test_offline_response_location_details():
    """Test location details parsing in fallback offline mode."""
    assistant = GeminiAssistant(api_key="")
    query = "Tell me about academic block 1"
    
    response, context = assistant.get_response(query)
    
    assert response["show_route"] is False
    assert "Academic Block 1" in response["text"]
    assert "Acad 1" in response["locations"]

def test_offline_response_fallback_help():
    """Test fallback details list returned if query doesn't match any patterns."""
    assistant = GeminiAssistant(api_key="")
    query = "What is the weather today?"
    
    response, context = assistant.get_response(query)
    
    assert response["show_route"] is False
    assert response["query_understood"] is False
    assert "Campus Navigation Help" in response["text"]
