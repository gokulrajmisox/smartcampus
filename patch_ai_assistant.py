import re
import os

with open('src/ai_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add json import if not there
if 'import json' not in content:
    content = content.replace('import os', 'import os\nimport json')

# Replace campus_info initialization
campus_info_pattern = re.compile(r'self\.campus_info = \{.*?\n        }', re.DOTALL)

init_block = """
        self.campus_info = {}
        try:
            with open("campus_data/demo_locations.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                for loc in data.get("locations", []):
                    self.campus_info[loc["name"]] = {
                        "name": loc["name"],
                        "location": loc.get("building", ""),
                        "hours": "Variable",
                        "facilities": ["Accessible" if loc.get("accessibility", {}).get("wheelchair") else "Standard"],
                        "nearby": loc.get("aliases", []),
                        "description": loc.get("description", "")
                    }
        except Exception as e:
            logger.error(f"Error loading demo locations in assistant: {e}")

        self.roles_data = {}
        try:
            with open("campus_data/roles.json", "r", encoding="utf-8") as f:
                self.roles_data = json.load(f).get("roles", {})
        except Exception as e:
            logger.error(f"Error loading roles: {e}")
"""

content = campus_info_pattern.sub(init_block.strip(), content)

# Also update the prompt in _handle_general_query
# The method _handle_general_query(self, query: str) needs the role context if we pass it.
# Let's change the signature to include `role: str = "Student"` and pass it.
content = re.sub(r'def _handle_general_query\(self, query: str\)', r'def _handle_general_query(self, query: str, role: str = "Student")', content)

prompt_block_pattern = re.compile(r'prompt = f"""You are a helpful campus navigation assistant.*?feature\."""', re.DOTALL)
new_prompt = r'''
                role_info = self.roles_data.get(role, {})
                role_focus = role_info.get("focus", "general campus navigation")
                
                prompt = f"""You are CampusAI, an inclusive and intelligent Smart Campus Copilot.
Your current user role is: {role}. You should focus your answers on: {role_focus}.

Answer the user's question about the campus using the provided information.
IMPORTANT: You support Multilingual queries. If the user asks in Tamil or Hindi, you MUST reply in that language. Otherwise, reply in English.

{campus_context}

User Question: {query}

Please provide a helpful, action-oriented response. If the question is about navigation, explicitly suggest they use the "Find Path" route planning feature in the sidebar. Do NOT hallucinate information not provided."""
'''

content = prompt_block_pattern.sub(new_prompt.strip(), content)

# We also need to update `get_response` to accept `role: str = "Student"`
content = re.sub(r'def get_response\(self, user_query: str, context: Optional\[Dict\[str, Any\]\] = None\)', r'def get_response(self, user_query: str, context: Optional[Dict[str, Any]] = None, role: str = "Student")', content)

# And pass it down to _handle_general_query
content = re.sub(r'self\._handle_general_query\(user_query\)', r'self._handle_general_query(user_query, role)', content)

with open('src/ai_assistant.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ai_assistant.py")
