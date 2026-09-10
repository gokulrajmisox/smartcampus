from google import genai
from google.genai import types
from typing import Dict, Any, Optional, List, Tuple
import re
import os
from datetime import datetime
from difflib import SequenceMatcher
from src.logger import logger

def get_string_similarity(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

def normalize_location_name(name: str) -> str:
    """Normalize location name for better matching."""
    return re.sub(r'[^a-z0-9]', '', name.lower())

class GeminiAssistant:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini AI assistant with campus knowledge."""
        # Use provided API key or fallback to environment variables
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Gemini Client successfully initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini GenAI Client: {e}", exc_info=True)
                self.client = None
        else:
            logger.warning("No Gemini API key provided. Running assistant in local offline fallback mode.")
            self.client = None
            
        self.campus_info = {
            "Flag post": {
                "name": "Main Flag Post",
                "location": "Campus Entrance",
                "hours": "24/7",
                "facilities": ["Information Board", "Security Post"],
                "nearby": ["Entry Gate", "Exit Gate"],
                "description": "The central flag post marking the campus entrance"
            },
            "Entry gate": {
                "name": "Main Entry Gate",
                "location": "Campus Perimeter",
                "hours": "24/7",
                "facilities": ["Security Booth", "Visitor Registration", "Information Desk"],
                "nearby": ["Flag Post", "Check Post 1"],
                "description": "Primary entrance point with security checkpoints"
            },
            "Exit gate": {
                "name": "Exit Gate",
                "location": "Campus Perimeter",
                "hours": "24/7",
                "facilities": ["Security Booth", "Vehicle Check Point"],
                "nearby": ["Flag Post", "Check Post 2"],
                "description": "Main exit point from campus"
            },
            "Check post 1": {
                "name": "Check Post 1",
                "location": "North Campus",
                "hours": "24/7",
                "facilities": ["Security Check", "Visitor Registration"],
                "nearby": ["Entry Gate", "Acad 1"],
                "description": "Northern security checkpoint"
            },
            "Check post 2": {
                "name": "Check Post 2",
                "location": "South Campus",
                "hours": "24/7",
                "facilities": ["Security Check", "Information Desk"],
                "nearby": ["Exit Gate", "Acad 2"],
                "description": "Southern security checkpoint"
            },
            "Acad 1": {
                "name": "Academic Block 1",
                "location": "Academic Zone",
                "hours": "7:00 AM - 6:00 PM",
                "facilities": ["Classrooms", "Labs", "Faculty Offices", "Seminar Halls"],
                "nearby": ["Library", "Faculty Block"],
                "description": "Primary academic building with modern facilities"
            },
            "Acad 2": {
                "name": "Academic Block 2",
                "location": "Academic Zone",
                "hours": "7:00 AM - 6:00 PM",
                "facilities": ["Lecture Halls", "Computer Labs", "Study Areas"],
                "nearby": ["Library", "Food Court"],
                "description": "Secondary academic building focusing on specialized courses"
            },
            "Library": {
                "name": "Central Library",
                "location": "Academic Zone",
                "hours": "8:00 AM - 10:00 PM",
                "facilities": ["Reading Rooms", "Digital Library", "Group Study Areas", "Research Section"],
                "nearby": ["Acad 1", "Acad 2"],
                "description": "Multi-story library with extensive collection and study spaces"
            },
            "Food Court": {
                "name": "Campus Food Court",
                "location": "Student Zone",
                "hours": "7:30 AM - 9:00 PM",
                "facilities": ["Multiple Food Stalls", "Seating Area", "Vending Machines"],
                "nearby": ["Library", "Hostel Block"],
                "description": "Central dining facility with diverse food options"
            },
            "Faculty Block": {
                "name": "Faculty Block",
                "location": "Academic Zone",
                "hours": "9:00 AM - 5:00 PM",
                "facilities": ["Faculty Offices", "Conference Rooms", "Meeting Areas"],
                "nearby": ["Acad 1", "Library"],
                "description": "Dedicated building for faculty offices and administrative work"
            },
            "Hostel Block": {
                "name": "Student Hostel",
                "location": "Residential Zone",
                "hours": "24/7",
                "facilities": ["Dormitories", "Common Rooms", "Laundry", "Recreation Areas"],
                "nearby": ["Food Court", "Sports Facilities"],
                "description": "Student accommodation with modern amenities"
            },
            "Cricket Ground": {
                "name": "Cricket Ground",
                "location": "Sports Zone",
                "hours": "6:00 AM - 7:00 PM",
                "facilities": ["Cricket Field", "Practice Nets", "Pavilion"],
                "nearby": ["Football Ground", "Basketball Court"],
                "description": "Regulation-size cricket ground with practice facilities"
            },
            "Basket Ball": {
                "name": "Basketball Court",
                "location": "Sports Zone",
                "hours": "6:00 AM - 7:00 PM",
                "facilities": ["Basketball Court", "Seating Area", "Floodlights"],
                "nearby": ["Volleyball Court", "Tennis Court"],
                "description": "Standard basketball court with spectator seating"
            },
            "Volley Ball": {
                "name": "Volleyball Court",
                "location": "Sports Zone",
                "hours": "6:00 AM - 7:00 PM",
                "facilities": ["Volleyball Court", "Practice Area"],
                "nearby": ["Basketball Court", "Tennis Court"],
                "description": "Regulation volleyball court with practice areas"
            },
            "Tennis Ball": {
                "name": "Tennis Court",
                "location": "Sports Zone",
                "hours": "6:00 AM - 7:00 PM",
                "facilities": ["Tennis Courts", "Practice Wall", "Equipment Room"],
                "nearby": ["Volleyball Court", "Basketball Court"],
                "description": "Professional tennis courts with practice facilities"
            },
            "Foot Ball": {
                "name": "Football Ground",
                "location": "Sports Zone",
                "hours": "6:00 AM - 7:00 PM",
                "facilities": ["Football Field", "Practice Area", "Changing Rooms"],
                "nearby": ["Cricket Ground", "Rest Area"],
                "description": "Full-size football field with training areas"
            },
            "Rest Area": {
                "name": "Campus Rest Area",
                "location": "Central Campus",
                "hours": "24/7",
                "facilities": ["Benches", "Shade Areas", "Water Points", "Vending Machines"],
                "nearby": ["Food Court", "Sports Zone"],
                "description": "Outdoor relaxation areas spread across campus"
            }
        }
        
        self.navigation_patterns = [
            r'(?:how (?:do|can|to))?\s*(?:get|go|walk|reach)\s+(?:from\s+)?([\w\s]+)\s+to\s+([\w\s]+)',
            r'(?:show|find|give)\s+(?:me\s+)?(?:the\s+)?(?:route|path|way|directions?)\s+(?:from\s+)?([\w\s]+)\s+to\s+([\w\s]+)',
            r'directions?\s+(?:from\s+)?([\w\s]+)\s+to\s+([\w\s]+)'
        ]

    def get_response(self, query: str, context: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Process user query and return the response and updated context."""
        logger.info(f"Processing AI assistant query: '{query}'")
        try:
            if context is None:
                context = {
                    'last_location': None,
                    'last_query_type': None,
                    'conversation_history': []
                }
                
            query_lower = query.lower()
            response = self._initialize_response()
            
            locations = self._extract_locations(query_lower, context)
            
            if self._is_navigation_query(query_lower):
                response.update(self._handle_navigation_query(query_lower, locations))
            elif locations:
                response.update(self._handle_location_query(locations[0], query_lower))
            else:
                response.update(self._handle_general_query(query_lower))
            
            # Update context
            if response['locations']:
                context['last_location'] = response['locations'][-1]
            context['conversation_history'].append({
                'timestamp': response['timestamp'],
                'query_understood': response['query_understood']
            })
            
            return response, context
            
        except Exception as e:
            logger.error(f"Error handling query assistant: {e}", exc_info=True)
            err_res = self._create_error_response(str(e))
            return err_res, context or {}

    def _extract_locations(self, query: str, context: Dict) -> list:
        """Extract locations using enhanced fuzzy matching."""
        locations = []
        
        for pattern in self.navigation_patterns:
            matches = re.search(pattern, query)
            if matches:
                potential_locations = [loc.strip() for loc in matches.groups() if loc]
                for pot_loc in potential_locations:
                    best_match = self._find_best_matching_location(pot_loc)
                    if best_match:
                        locations.append(best_match)
        
        if not locations:
            words = query.split()
            for word in words:
                best_match = self._find_best_matching_location(word)
                if best_match and best_match not in locations:
                    locations.append(best_match)
        
        if not locations and ('here' in query or 'there' in query):
            if context.get('last_location'):
                locations.append(context['last_location'])
        
        return locations

    def _find_best_matching_location(self, query_term: str, threshold: float = 0.6) -> Optional[str]:
        """Find best matching location using fuzzy matching."""
        best_match = None
        highest_score = threshold
        query_normalized = normalize_location_name(query_term)
        
        for loc_key, loc_info in self.campus_info.items():
            score = get_string_similarity(query_normalized, normalize_location_name(loc_key))
            if score > highest_score:
                highest_score = score
                best_match = loc_key
            
            score = get_string_similarity(query_normalized, normalize_location_name(loc_info['name']))
            if score > highest_score:
                highest_score = score
                best_match = loc_key
            
            variations = [
                loc_key.replace('_', ' '),
                loc_info['name'].lower(),
                loc_key.replace('block', '').strip(),
                loc_key.replace('court', '').strip(),
                loc_key.replace('ground', '').strip()
            ]
            
            for variation in variations:
                score = get_string_similarity(query_normalized, normalize_location_name(variation))
                if score > highest_score:
                    highest_score = score
                    best_match = loc_key
        
        return best_match

    def _initialize_response(self) -> Dict[str, Any]:
        """Initialize response with metadata."""
        return {
            "text": "",
            "show_route": False,
            "start": None,
            "end": None,
            "locations": [],
            "timestamp": datetime.now().isoformat(),
            "query_understood": False
        }

    def _is_navigation_query(self, query: str) -> bool:
        """Enhanced navigation query detection."""
        return any(re.search(pattern, query) for pattern in self.navigation_patterns)

    def _handle_navigation_query(self, query: str, locations: list) -> Dict[str, Any]:
        """Handle navigation queries with enhanced location matching."""
        if len(locations) >= 2:
            start_loc, end_loc = locations[0], locations[1]
            start_info = self.campus_info[start_loc]
            end_info = self.campus_info[end_loc]
            
            return {
                "text": f"### 🗺️ Navigation Instructions\nI'll help you get from {start_info['name']} to {end_info['name']}.\n\n**Start Point:** {start_info['location']}\n**Destination:** {end_info['location']}\n**Notable Landmarks:** Near {', '.join(end_info['nearby'])}\n\n*The route is now displayed on the map*\n\n**Additional Information:**\n- Destination Hours: {end_info['hours']}\n- Available Facilities: {', '.join(end_info['facilities'])}",
                "show_route": True,
                "start": start_loc,
                "end": end_loc,
                "locations": locations,
                "query_understood": True
            }
        
        return {
            "text": "### 🤔 Need More Information\nPlease specify both start and destination locations. For example:\n- \"How do I get from the library to the cafeteria?\"\n- \"Show me the way from the entrance to the academic block\"\n",
            "show_route": False,
            "locations": []
        }

    def _handle_location_query(self, location: str, query: str) -> Dict[str, Any]:
        """Handle queries about specific locations."""
        info = self.campus_info[location]
        
        if "hour" in query or "time" in query or "open" in query:
            response_text = f"### ⏰ {info['name']} Hours\n- **Operating Hours:** {info['hours']}\n- **Location:** {info['location']}"
        elif "facilities" in query or "available" in query:
            response_text = f"### 🏢 {info['name']} Facilities\n- **Available Facilities:**\n" + "\n".join([f"  • {f}" for f in info['facilities']])
        else:
            response_text = f"### 📍 {info['name']}\n- **Description:** {info['description']}\n- **Location:** {info['location']}\n- **Hours:** {info['hours']}\n- **Nearby:** {', '.join(info['nearby'])}"
            
        return {
            "text": response_text,
            "show_route": False,
            "locations": [location]
        }

    def _handle_general_query(self, query: str) -> Dict[str, Any]:
        """Handle general queries about campus using Gemini AI."""
        if self.client:
            try:
                campus_context = "Campus Information:\n"
                for loc, info in self.campus_info.items():
                    campus_context += f"- {info['name']} ({loc}): {info['description']}\n"
                    campus_context += f"  Hours: {info['hours']}, Facilities: {', '.join(info['facilities'])}\n"
                
                prompt = f"""You are a helpful campus navigation assistant. Answer the user's question about the campus using the provided information.

{campus_context}

User Question: {query}

Please provide a helpful, informative response about the campus. If the question is about navigation, suggest they use the route planning feature."""

                logger.info("Querying Gemini GenAI model...")
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                
                return {
                    "text": response.text or "I apologize, but I couldn't generate a response. Please try asking in a different way.",
                    "show_route": False,
                    "locations": [],
                    "query_understood": True
                }
            except Exception as e:
                logger.error(f"Gemini generation error: {e}", exc_info=True)
                pass
        
        return {
            "text": """### 🎓 Campus Navigation Help
I can help you with:
1. **Finding Routes:** Ask "How do I get from X to Y?"
2. **Location Info:** Ask "Tell me about the library"
3. **Facilities:** Ask "What facilities are in X?"
4. **Hours:** Ask "When is X open?"

**Available Locations:**\n""" + "\n".join([f"- {info['name']}" for info in self.campus_info.values()]),
            "show_route": False,
            "locations": [],
            "query_understood": False
        }

    def _create_error_response(self, error: str) -> Dict[str, Any]:
        """Create a helpful error response."""
        return {
            "text": f"### ❌ I encountered an issue\nI apologize, but I had trouble processing your request. Please try again later.\n\nTechnical details: {error}",
            "show_route": False,
            "start": None,
            "end": None,
            "locations": [],
            "query_understood": False
        }
