# CampusAI — Hackathon Judge Demo Script

## 90-Second Presentation

**Hello, this is CampusAI, an inclusive smart-campus navigation copilot.**

The problem we address is simple: on a large campus, students, visitors, and staff often know where they want to go but do not know the best route, the available facilities, or whether the route is accessible. Existing campus maps are usually static, difficult to search, and disconnected from conversational assistance.

CampusAI combines three capabilities in one Streamlit application. First, it loads real campus road data from OpenStreetMap XML. Second, it calculates routes using BFS, DFS, Uniform Cost Search, and multiple A* variants. Third, it provides a role-aware Gemini assistant that understands natural-language questions such as, “How do I get from the Main Gate to the Library?” and converts recognized locations into an actionable route.

The application supports different user roles, including students, faculty, visitors, security, maintenance, and support staff. It also includes an accessibility-route mode and location information for campus facilities such as the Library, Cafeteria, CSE Laboratory, Medical Center, Hostel, and Main Gate.

The most important user flow is the navigation flow. A user selects a starting point and destination, presses **Route**, and receives a highlighted path on an interactive Folium map along with distance, estimated walking time, start and destination markers, and explored graph nodes.

We also fixed the production deployment issue. The Docker image now includes the campus data, map assets, and Streamlit configuration. The Render deployment uses Python 3.11 through Docker and is live at:

**https://smartcampus-docker.onrender.com**

The application has been validated with **14 automated tests**, including route-distance checks and map-layer rendering checks. The latest verified route from Main Gate to Library is approximately 470 meters.

For imagery, the application provides a reliable OpenStreetMap street layer and an Esri satellite layer. We also prepared an optional Planet Basemaps layer. The Planet API key is configured securely in Render, but the account currently returns no accessible mosaics, so we do not falsely claim that Planet imagery is active. Once the Planet account grants Basemaps access and provides a mosaic ID, that layer can be enabled through configuration without changing the routing system.

**CampusAI’s key innovation is the combination of conversational AI, graph-based navigation, accessibility support, role-aware responses, and deployable campus data in one practical system.**

## Live Demonstration Flow

1. Open **https://smartcampus-docker.onrender.com**.
2. Select **Navigate** from the sidebar.
3. Choose **Main Gate** as the starting point.
4. Choose **Library** as the destination.
5. Press **Route**.
6. Point out the highlighted route, markers, distance, estimated walking time, and layer control.
7. Return to **Ask CampusAI**.
8. Ask: **“How do I get from the Main Gate to the Library?”**
9. Show the natural-language response and the **Navigate** action.
10. Mention the accessibility toggle and role selector.

## Technical Summary for Judges

- **Frontend:** Streamlit
- **Interactive maps:** Folium and streamlit-folium
- **Routing data:** OpenStreetMap campus graph
- **Routing algorithms:** BFS, DFS, UCS, A* Euclidean, A* Manhattan, and A* Combined
- **AI assistant:** Google Gemini through the Google GenAI SDK
- **Deployment:** Docker on Render
- **Security:** API keys stored in Render environment variables; no secrets committed to GitHub
- **Validation:** 14 automated tests passing
- **Repository:** https://github.com/gokulrajmisox/smartcampus

## If Asked About Planet Imagery

Use this precise answer:

> “We integrated the Planet configuration path and added an optional Planet tile layer, but the supplied Planet account currently returns no accessible mosaics from the Basemaps API. Therefore, the live demo uses the reliable OpenStreetMap and Esri layers. We intentionally do not claim Planet imagery is active until the account has Basemaps access and provides an authorized mosaic ID.”

## Closing Statement

**CampusAI turns a static campus map into an intelligent, inclusive, and actionable navigation assistant. It does not only tell users where a place is; it understands the user’s intent, calculates a route, displays it visually, and adapts the experience to the user’s role and accessibility needs.**
