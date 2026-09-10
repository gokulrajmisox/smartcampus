# CampusAI Architecture

## Core Philosophy
CampusAI flips the traditional campus app model. Instead of providing static maps or PDFs of rules, CampusAI is an **action-oriented** Copilot. You tell it what you want to do, and it figures out the path.

## High-Level Pipeline
1. **User Input** (Natural Language + UI Controls)
2. **Intent Engine** (Gemini 1.5 Flash 8b)
   - Extracts start/end destinations
   - Identifies roles (Student, Security)
   - Understands language context (Tamil, Hindi, English)
3. **Graph Engine** (OSMnx / NetworkX)
   - Parses OpenStreetMap XML
   - Projects geographical coordinates
4. **Accessibility Filter** 
   - Dynamically prunes graph edges based on `accessibility_mode` (avoids stairs/steps)
5. **Pathfinding** (A*, UCS, BFS, DFS)
6. **Rendering** (Streamlit + Folium)

## Data Layer
- `campus_data/demo_locations.json`: Contains verified locations, preventing AI hallucination.
- `campus_data/roles.json`: Contains persona-based contexts.
