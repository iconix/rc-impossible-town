from pydantic import BaseModel, Field
from typing import Union, Literal, Optional, List, Set
from enum import Enum


class ItemType(str, Enum):
    SWORD = "Sword"
    STONE = "Stone"
    KEY = "Key"
    TREASURE = "Treasure"


class AgentName(str, Enum):
    SEEKER = "Seeker"
    KNOWER = "Knower"
    GUIDE = "Guide"
    EXPLORER = "Explorer"
    WANDERER = "Wanderer"


class LocationName(str, Enum):
    CITY = "City"
    FIELD = "Field"
    FOREST = "Forest"
    CAVE = "Cave"
    MOUNTAIN = "Mountain"
    BEACH = "Beach"


class ItemLocation(BaseModel):
    item_type: ItemType
    location: LocationName


class Knowledge(BaseModel):
    item_locations: List[ItemLocation] = Field(
        default_factory=list
    )  # Where items are located
    places: Set[str] = Field(default_factory=set)  # Known places in the world
    agents: List[str] = Field(default_factory=list)  # Known agents


class Information(BaseModel):
    information: set[Knowledge]


class SeekMotivation(BaseModel):
    motivation_name: str = "Seek item"
    item_type: ItemType

    def get_rules(self) -> str:
        return """SEEK MOTIVATION RULES (HIGHEST PRIORITY):
1. If you're in a location where you believe your sought item is:
   - You MUST IMMEDIATELY use search_action to look for it
   - Do not use any other action type when in a location with your sought item
   - Do not leave the location without searching first
2. If you don't know where your sought item is, ASK other agents about it
3. Focus your dialogue on finding your sought item
4. Only travel to locations where you think your sought item might be
5. Finding your sought item will make you happier and increase your reputation."""


class BeHelpfulMotivation(BaseModel):
    motivation_name: str = "Be helpful"

    def get_rules(self) -> str:
        return """BE HELPFUL MOTIVATION RULES (HIGHEST PRIORITY):
1. You MUST share any knowledge you have when asked
2. Be thorough when checking your knowledge to help others
3. Focus your dialogue on assisting others and sharing information, rather than asking for information yourself.
4. Doing a good job will make you more helpful and increase your reputation."""


class BaseAction(BaseModel):
    type: str
    message: str
    target_agent: AgentName
    end_turn: bool = True

    @classmethod
    def format_spec(cls) -> str:
        return ""

    @classmethod
    def get_rules(cls) -> str:
        return ""


class DialogueAction(BaseAction):
    type: Literal["dialogue_action"] = "dialogue_action"
    is_question: bool
    knowledge: Optional[Union[Knowledge, str]] = None
    knowledge_desired: Optional[str] = None

    @classmethod
    def format_spec(cls) -> str:
        return """DIALOGUE ACTION
   Required fields:
   - type: "dialogue_action"
   - target_agent: (name of agent to talk to)
   - message: (your natural dialogue)
   - is_question: true when asking, false when responding
   - knowledge: (include knowledge when sharing information, string description, or null)
   - knowledge_desired: (type of item you're asking about, null when not asking)"""

    @classmethod
    def get_rules(cls) -> str:
        return """DIALOGUE RULES:
1. When someone asks you a question, you MUST respond with a direct answer (not another question):
   - If you have the knowledge they want, share it
   - If you don't have the knowledge, try to answer the question as best as you can
2. Before responding to questions about items, carefully check your knowledge list for information about the item
3. Create natural, conversational dialogue - be friendly and clear
4. Don't repeat information that was just shared
5. Share knowledge directly without extra commentary"""


class TravelAction(BaseAction):
    type: Literal["travel_action"] = "travel_action"
    location: LocationName

    @classmethod
    def format_spec(cls) -> str:
        return """TRAVEL ACTION
   Required fields:
   - type: "travel_action"
   - location: (location to travel to)
   - message: (explain where and why you're going)
   - target_agent: (who to inform about your travel)"""

    @classmethod
    def get_rules(cls) -> str:
        return """TRAVEL RULES:
1. When using travel_action, explain where and why you're traveling
2. After traveling to a location where you believe an item is, use search_action to look for it
3. When you know where your sought item is, travel there immediately"""


class SearchAction(BaseAction):
    type: Literal["search_action"] = "search_action"
    item_type: ItemType
    # TODO: add location? so we can check if the search is for the current location

    @classmethod
    def format_spec(cls) -> str:
        return """SEARCH ACTION
   Required fields:
   - type: "search_action"
   - item_type: (type of item to search for: "Sword" or "Stone")
   - message: (describe your search)
   - target_agent: (who to inform about your search)
   - end_turn: true/false (defaults to true)"""

    @staticmethod
    def get_rules() -> str:
        return """SEARCH RULES:
1. You can only search for items in your current location
2. If you're in a location where you believe your sought item is:
   - You MUST IMMEDIATELY use search_action to look for it
   - Do not use any other action type when in a location with your sought item
   - Do not leave the location without searching first"""


class ValidationResult(BaseModel):
    is_valid: bool = Field(
        description="Whether the action is valid in the current world state"
    )
    reason: str = Field(
        description="Detailed explanation of why the action is valid or invalid"
    )


class NotepadAction(BaseAction):
    type: Literal["notepad_action"] = "notepad_action"
    note: str
    target_agent: Optional[AgentName] = ""

    @classmethod
    def format_spec(cls) -> str:
        return """NOTEPAD ACTION
   Required fields:
   - type: "notepad_action"
   - note: (content to remember)
   - message: (why you're making this note)

   Optional fields:
   - target_agent: (who to inform about your note-taking, optional)
   - end_turn: true/false (defaults to true)"""

    @classmethod
    def get_rules(cls) -> str:
        return """NOTEPAD RULES:
1. Use notepad to record ALL important information you want to remember
2. CRITICAL: You MUST make a note when you learn:
   - Where an item is located
   - New information about your sought item
   - Important facts from other agents
3. Keep notes concise and focused on actionable information
4. Notes persist throughout the simulation - they are your memory
5. If you don't make notes, you WILL forget critical information"""


class GiveAction(BaseAction):
    """Action for giving an item to another agent"""

    type: Literal["give_action"] = "give_action"
    target_agent: AgentName  # Agent to give the item to
    item_type: ItemType  # Item to give

    @staticmethod
    def format_spec() -> str:
        """Format the give action spec for LLM consumption"""
        return """type: give_action
Description: Give an item from your inventory to another agent.
Required fields:
- target_agent: The name of the agent to give the item to
- item_type: The type of item to give (must be in your inventory)

Example:
{
  "type": "give_action",
  "target_agent": "Seeker",
  "item_type": "Sword"
}"""

    @staticmethod
    def get_rules() -> str:
        """Rules for using give action"""
        return """GIVE ACTION RULES:
1. You can only give items that are in your inventory (acquired_items)
2. The agent you're giving to must be in the same location as you
3. Use this action when:
   - Another agent is seeking an item you have
   - You want to help another agent achieve their goal
   - You need to transfer an item for strategic reasons
4. Be specific about which item you're giving and to whom
5. You cannot give an item and then immediately ask for it back
6. Giving should make strategic sense based on both agents' motivations"""


# Action icons for UI and console display
ACTION_ICONS = {
    "dialogue": "💬 ",  # Chat icon
    "dialogue_action": "💬 ",  # Chat icon (alternative key)
    "travel": "🚶 ",  # Walking icon
    "travel_action": "🚶 ",  # Walking icon (alternative key)
    "search": "🔍 ",  # Magnifying glass
    "search_action": "🔍 ",  # Magnifying glass (alternative key)
    "found": "✓ ",  # Checkmark
    "meeting": "👥 ",  # People icon
    "knowledge": "💡 ",  # Lightbulb
    "location": "🗺️ ",  # Map
    "notepad": "📝 ",  # Notepad
    "notepad_action": "📝 ",  # Notepad (alternative key)
    "give": "🎁 ",  # Gift box
    "give_action": "🎁 ",  # Gift box (alternative key)
    "system": "⚙️ ",  # Gear icon
    "state": "📊 ",  # Bar chart
    "action_start": "🔄 ",  # Refresh
    "turn": "⏱️ ",  # Timer
    "memory_keeper": "🧠 ",  # Brain
}

# Text-based fallbacks for platforms that don't support emoji
ACTION_SYMBOLS = {
    "dialogue": "[TALK] ",
    "dialogue_action": "[TALK] ",
    "travel": "[MOVE] ",
    "travel_action": "[MOVE] ",
    "search": "[SRCH] ",
    "search_action": "[SRCH] ",
    "found": "[FIND] ",
    "meeting": "[MEET] ",
    "knowledge": "[INFO] ",
    "location": "[LOCN] ",
    "notepad": "[NOTE] ",
    "notepad_action": "[NOTE] ",
    "give": "[GIVE] ",
    "give_action": "[GIVE] ",
    "system": "[SYS] ",
    "state": "[STAT] ",
    "action_start": "[ACT>] ",
    "turn": "[TURN] ",
    "memory_keeper": "[MEM] ",
}
