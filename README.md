# AI Campus Navigator

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)](https://streamlit.io)
[![Gemini AI](https://img.shields.io/badge/AI-Gemini--Flash-orange)](https://deepmind.google/technologies/gemini/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

The AI Campus Navigator is an intelligent, highly interactive routing and pathfinding application explicitly designed to help students, faculty, and visitors seamlessly navigate sprawling, complex university campuses. To achieve millimeter precision, the system natively parses incredibly rich OpenStreetMap (OSM) XML data. It structures this vast geographical information into highly optimized, navigable graph networks using powerful Python libraries like NetworkX and OSMnx, ensuring that every walkway, building entrance, and accessibility ramp is accurately represented in the routing matrix.

Under the hood, the application serves as an advanced sandbox for graph theory and spatial analysis. Users can dynamically toggle between multiple sophisticated graph traversal algorithms to find their optimal route. This includes fundamental approaches like Breadth-First Search (BFS) and Depth-First Search (DFS), up to cost-aware algorithms like Uniform Cost Search (UCS) and the highly optimized, heuristic-driven A* algorithm. This flexibility ensures that the platform can instantly calculate the shortest, fastest, or most accessible paths regardless of campus size or topological complexity.

What truly elevates this application is its seamless integration with the advanced Google Gemini 2.5 Flash AI model. This provides users with a powerful natural language interface, allowing them to ask conversational, context-aware questions about campus locations, historical building information, and optimal paths. Whether a user is looking for the nearest open cafeteria or the most accessible route to a specific lecture hall, the Gemini-powered assistant interprets the request and coordinates with the routing engine to deliver precise, accessible answers through a clean, responsive Streamlit web interface.

---

## ✨ Features

- **🗺️ Interactive Map rendering** — Generates interactive HTML maps with custom route paths overlaid dynamically using Folium.
- **🧭 Dynamic Algorithm Picker** — Interactive comparisons of standard pathfinding solutions for the same source-destination nodes.
- **💬 Natural Language Assistant** — Integrates Gemini AI to translate informal questions ("how do I get to hostel from main gate?") into source and destination nodes automatically.
- **📈 Route Metrics** — Calculates total distance, estimated walking time, and list of nodes/waypoints passed.

### 🧭 Pathfinding Algorithms Comparison

| Algorithm | Heuristic | Optimality | Completeness | Complexity (Worst-Case) |
| :--- | :--- | :--- | :--- | :--- |
| **Breadth-First Search (BFS)** | No | Yes (if uniform edge costs) | Yes | O(\|V\| + \|E\|) |
| **Depth-First Search (DFS)** | No | No | No (in infinite spaces) | O(\|V\| + \|E\|) |
| **Uniform Cost Search (UCS)** | No | Yes | Yes | O(\|E\| + \|V\| log \|V\|) |
| **A\* Search** | Yes | Yes (if h(n) is admissible) | Yes | O(\|E\| + \|V\| log \|V\|) |

---

## 🏗️ Project Architecture

```
ai-campus-navigator/
├── LICENSE
├── README.md
├── app.py                     # Minimal Streamlit Main Entrypoint
├── pyproject.toml             # Python Package configuration
├── uv.lock                    # Fast Package Manager lockfile
├── Dockerfile                 # Multi-stage Docker Container blueprint
├── docker-compose.yml         # Compose Orchestrator configuration
├── .env.example               # Template Environment credentials
├── src/                       # Core Source Directory
│   ├── logger.py              # Structured JSON logging service
│   ├── pathfinding.py         # Pathfinding algorithms & POI definitions
│   ├── ai_assistant.py        # Gemini AI Assistant engine
│   └── ui/                    # Streamlit component modules
│       ├── sidebar.py         # Sidebar rendering & chat inputs
│       ├── map_viewer.py      # Map layer rendering
│       └── comparison.py      # Benchmarking matrices renderer
├── tests/                     # Automated test suite
│   ├── test_pathfinding.py    # Unit tests for BFS, DFS, UCS, A* search
│   └── test_ai_assistant.py   # Unit tests for NLP matching and normalization
└── docs/                      # Mapping datasets & documents
    ├── Extracted_Edges__from_KML_LineStrings_.csv
    ├── Extracted_Nodes__from_KML_.csv
    ├── map.png
    └── ucs_hostel_path.png
```

### 🔀 System Data Flow

```mermaid
graph TD
    OSM[attached_assets/map.osm] -->|ox.graph_from_xml| Pathfinder[src/pathfinding.py]
    UserQuery[User Chat Input] -->|gemini.get_response| AI[src/ai_assistant.py]
    AI -->|gemini-2.5-flash| GoogleAI[Google GenAI API]
    AI -->|Parsed locations| Pathfinder
    Pathfinder -->|nx.shortest_path| Algos[BFS, DFS, UCS, A* Search]
    Algos -->|Route metrics & paths| View[src/ui/map_viewer.py]
    View -->|st_folium| Map[Interactive Folium Map layer]
```

---

## 🛠️ Tech Stack

| Layer | Technology | Detail |
| :--- | :--- | :--- |
| **GUI Framework** | Streamlit | Rapid Python-native user dashboard |
| **Network Analysis**| NetworkX, OSMnx | High-performance graph layouts and computations |
| **Maps Renderer** | Folium | Leaflet-based interactive HTML mapping layers |
| **AI Ingestion** | Google GenAI SDK | Gemini 2.5 Flash model |
| **Package Manager** | UV | Modern, ultra-fast Python environment engine |

---

## 🚀 Getting Started & Installation

### Prerequisites
- **Python 3.11+**
- **uv** (Install via `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Setup & Run

```bash
# Clone the repository
git clone https://github.com/vemana4/ai-campus-navigator.git
cd ai-campus-navigator

# Install dependencies using uv
uv sync

# Configure Gemini API credentials
mkdir -p .streamlit
echo 'GEMINI_API_KEY = "your-api-key-here"' > .streamlit/secrets.toml

# Launch the interactive pathfinder
uv run streamlit run app.py
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE) - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/vemana4">Vemana Hemanth Babu</a>
</p>
