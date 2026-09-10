import os

content = """# CampusAI – Inclusive Smart Campus Copilot

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40.0-red.svg)](https://streamlit.io)
[![Gemini AI](https://img.shields.io/badge/AI-Gemini--3.5--Flash-orange)](https://deepmind.google/technologies/gemini/)

**"One intelligent layer for a more accessible campus."**

CampusAI is a polished hackathon-ready smart campus navigation system. It transforms raw OpenStreetMap (OSM) XML data into an interactive, AI-powered routing engine that understands natural language, respects accessibility needs, and adapts to different user roles (Student, Security, Maintenance).

Most campus systems are built around information. CampusAI is built around **ACTION**. You don't search a map; you simply ask: *"How do I get to the library without stairs?"* and CampusAI draws the path.

---

## ✨ Features

- **🗣️ Natural Language Routing:** Chat with the Gemini 3.5 AI to ask for directions. The AI will extract the intent and automatically plot the route on the map!
- **♿ Accessibility Mode:** Toggle "Accessible Route" to dynamically prune non-accessible edges (like stairs) from the graph search.
- **🌐 Multilingual Support:** Ask questions in English, Tamil, or Hindi. The AI responds contextually.
- **👷 Overlooked Workforce Mode:** A role selector tailors the experience for Students, Faculty, Visitors, Security, Maintenance, and Support Staff.
- **🚨 Emergency Mode:** Instant routing to the nearest medical center or security post.
- **🧠 Advanced Graph Algorithms:** Choose between A* (Euclidean/Manhattan/Combined), Dijkstra (UCS), BFS, and DFS for academic algorithm comparison.

---

## 🏗️ Architecture

```mermaid
graph TD
    UserQuery[User Chat Input] -->|Role + Context| AI[Gemini 3.5 Flash]
    AI -->|Extract Intent & POIs| RoutingEngine[OSM Pathfinder]
    AccessibilityToggle[Accessibility Mode] --> RoutingEngine
    RoutingEngine -->|A* Algorithm| MapUI[Folium / Streamlit Render]
    JSON[campus_data/demo_locations.json] --> AI
    JSON --> RoutingEngine
```

---

## 🚀 Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/vemana4/ai-campus-navigator.git
cd ai-campus-navigator
```

### 2. Configure Environment
Copy the example environment file and add your Gemini API Key.
```bash
cp .env.example .env
# Edit .env and insert GEMINI_API_KEY="your_api_key_here"
```

### 3. Install Dependencies & Run
Using `uv` (recommended):
```bash
uv sync
uv run streamlit run app.py
```

Or using pip:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -r pyproject.toml # manually install deps or use pip install .
streamlit run app.py
```

---

## 📂 Project Structure

- `app.py` - Streamlit entry point & dashboard layout.
- `src/pathfinding.py` - Core OSMnx graph routing engine.
- `src/ai_assistant.py` - Gemini AI integration, intent detection, and RAG.
- `campus_data/` - JSON stores for verified campus locations and roles (prevents hallucination).
- `docs/` - Hackathon presentation docs (Architecture, Innovation, Demo Script).
- `attached_assets/` - Contains the raw `.osm` OpenStreetMap XML graph.

---

## 🔬 Tech Stack
- **Frontend:** Streamlit, Folium
- **AI/LLM:** Google Gemini 3.5 Flash via `google-genai`
- **Routing:** OSMnx, NetworkX
- **Data:** JSON (No DB required for demo)

---

## 💡 Customizing for Your Campus

To use this for your own university:
1. Download an `.osm` export of your campus from [OpenStreetMap](https://www.openstreetmap.org/export).
2. Place it in `attached_assets/`.
3. Update `app.py` to point to the new `.osm` file.
4. Update `campus_data/demo_locations.json` with your building coordinates.

---
*Built for Track 2 – AI for Smart Campus*
"""
with open('README.md', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated README.md")
