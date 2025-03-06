from typing import List, Optional, Union, Set, Any, Literal
from pydantic import BaseModel, Field, TypeAdapter

from data import (
    AgentName,
    BaseAction,
    DialogueAction,
    NotepadAction,
    TravelAction,
    SearchAction,
    Knowledge,
    ItemLocation,
    SeekMotivation,
    BeHelpfulMotivation,
    ValidationResult,
    ItemType,
    GiveAction,
)
from llm_service import LLMService

MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
_llm_service = LLMService(provider="together", model_name=MODEL)


def configure_llm(provider: str, model_name: str, api_key: Optional[str] = None):
    """Configure the LLM service with provider and model"""
    global MODEL, _llm_service
    MODEL = model_name
    _llm_service.configure(provider, model_name, api_key)


class Agent(BaseModel):
    name: str
    current_location: str
    known_items: List[ItemType] = Field(default_factory=list)
    known_locations: Set[str] = Field(default_factory=set)
    known_agents: List[str] = Field(default_factory=list)
    motivation: Union[SeekMotivation, BeHelpfulMotivation]
    knowledge: Knowledge = Field(default_factory=Knowledge)
    acquired_items: List[ItemType] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    use_notepad_instead_of_knowledge: bool = Field(default=False)

    # This field won't be included in serialization
    logger: Optional[Any] = Field(default=None, exclude=True)

    def initialize_notepad(self):
        """Initialize the notepad with the agent's initial knowledge."""
        if not self.notes:  # Only initialize if notes are empty
            # Add item locations to notes
            for item_loc in self.knowledge.item_locations:
                self.notes.append(
                    f"I know that the {item_loc.item_type.value} is in the {item_loc.location.value}."
                )

            # Add known locations
            if self.known_locations:
                for location in self.known_locations:
                    self.notes.append(f"I know there is a place called {location}.")

            # Add known agents
            if self.known_agents:
                for agent in self.known_agents:
                    self.notes.append(f"I know about a fellow agent named {agent}.")

            # Add motivation-specific notes
            if hasattr(self.motivation, "item_type"):
                self.notes.append(
                    f"My goal is to find the {self.motivation.item_type.value}."
                )

            # Add current location note
            self.notes.append(f"I am currently in the {self.current_location}.")

            # If no substantive notes were created, add a default note
            if not self.notes:
                self.notes.append("I don't have any initial knowledge.")

    def produce_next_action(
        self,
        available_actions,
        global_past_actions,
        rejection_reason: Optional[str] = None,
    ) -> str:
        """Generate the next action for this agent"""
        # look through past actions to find dialogue directed at this agent
        recent_dialogue = []
        for past_action in global_past_actions[-5:]:
            for agent_name, action in past_action.items():
                try:
                    if (
                        action.action.type == "dialogue_action"
                        and action.action.target_agent == AgentName(self.name)
                    ):
                        recent_dialogue.append(
                            {
                                "from": agent_name,
                                "message": action.action.message,
                                "is_question": action.action.is_question,
                                "knowledge_desired": (
                                    action.action.knowledge_desired
                                    if action.action.is_question
                                    else None
                                ),
                                "knowledge_shared": action.action.knowledge is not None,
                            }
                        )
                except:
                    continue

        """
        if recent_dialogue:
            print(f"\n📨 Recent messages to {self.name}:")
            for msg in recent_dialogue:
                print(f"   From {msg['from']}: {msg['message']}")
        """

        # Create a modified state based on the flag
        if self.use_notepad_instead_of_knowledge:
            # Create a copy of the current state
            agent_state = self.model_dump(exclude={"logger"})

            # Replace knowledge with notes
            agent_state["knowledge"] = {
                "item_locations": [],
                "places": set(),
                "agents": [],
            }
            agent_state["notes_as_memory"] = self.notes
        else:
            agent_state = self.model_dump_json()

        prompt = f"""Choose an action based on your current state and recent dialogue:

Current state: {agent_state}

Recent dialogue directed at you: {recent_dialogue}

CRITICAL INSTRUCTION: If you are seeking an item and you are currently in a location where you believe that item is located, you MUST use the search_action.

{self.format_available_actions()}

{self.motivation.get_rules()}

MEMORY MANAGEMENT:
{"1. You are using your NOTEPAD instead of detailed knowledge. Consult your notes for critical information." if not self.use_notepad_instead_of_knowledge else "1. Consider using notepad_action to record important facts you want to remember."}
2. IMPORTANT: Whenever you receive information about item locations, you MUST immediately make a note of it using notepad_action.
3. IMPORTANT: When someone tells you where your sought item is located, you MUST first record this with notepad_action.
4. Good notes are concise and focus on key information like item locations.
5. Notepad actions NEVER end your turn - you must ALWAYS follow with another meaningful action.
6. IMPORTANT: If you don't make notes, you may forget critical information!

DIALOGUE PROCESSING:
1. When someone tells you where an item is located, you MUST record this information in your notepad first
2. After recording new information, act on it immediately (e.g., travel to the location)
3. Prioritize processing new information about your sought item above all else

EFFICIENCY RULES:
1. Don't state intentions - just take the action
2. When you receive useful information, act on it immediately - don't acknowledge receipt
3. Don't repeat information that was just shared
4. Share knowledge directly without extra commentary
5. When you know where your sought item is, travel there immediately
6. Be proactive - if you need information to achieve your motivation, ask questions first (but never in response to a question)

{DialogueAction.get_rules()}

{TravelAction.get_rules()}

{SearchAction.get_rules()}

{NotepadAction.get_rules()}

{GiveAction.get_rules()}

TURN MANAGEMENT:
1. DEFAULT BEHAVIOR: End your turn after ONE action unless you have an urgent reason to continue
2. Valid reasons to take multiple actions:
   - You MUST search immediately after traveling to a location with your sought item
   - You MUST respond to a direct question
   - You are in the middle of a critical information exchange
   - You MUST take notes and then act on new information about item locations
3. When ending turn, explain your reasoning clearly in the message

{f"PLEASE AVOID REPEATING THIS MISTAKE: {rejection_reason}" if rejection_reason else ""}

Choose your next action and respond with a valid JSON action that matches the required fields above. Make sure to use proper JSON formatting."""

        # print(prompt)
        print(f"\n🤖 {self.name} is thinking...")

        # Create a TypeAdapter for the available_actions
        action_adapter = TypeAdapter(available_actions)

        response = _llm_service.chat(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format=action_adapter.json_schema(),
        )

        return response["message"]["content"]

    def receive_action(
        self, action: BaseAction, agent: "Agent", item_locations: List[ItemLocation]
    ) -> None:
        """Update agent state based on received action"""
        try:
            action_type = action.type

            # update known_agents if we haven't seen this agent before
            if agent.name not in self.known_agents and agent.name != self.name:
                self.known_agents.append(agent.name)
                if self.use_notepad_instead_of_knowledge:
                    self.auto_note(f"I met a fellow agent named {agent.name}.")
                if self.logger:
                    self.logger.log_system_message(
                        "meeting", f"{self.name} met {agent.name}"
                    )
                else:
                    print(f"\n🤝 {self.name} met {agent.name}")

            if action_type == "search_action" and agent.name == self.name:
                item_type = action.item_type
                location_has_item = any(
                    loc.item_type == item_type
                    and loc.location.lower() == self.current_location.lower()
                    for loc in item_locations
                )

                if location_has_item:
                    # Special case for Treasure - requires having the Key
                    if item_type == ItemType.TREASURE and "Key" not in [
                        i for i in self.acquired_items
                    ]:
                        if self.logger:
                            self.logger.log_system_message(
                                "search",
                                f"{self.name} found the Treasure but needs a Key to unlock it!",
                            )
                        else:
                            print(
                                f"\n🔒 {self.name} found the Treasure but needs a Key to unlock it!"
                            )

                        # Add auto-note about needing a key
                        if self.use_notepad_instead_of_knowledge:
                            self.auto_note(
                                f"I found the Treasure in the {self.current_location}, but I need a Key to unlock it."
                            )

                        # Don't add the treasure to acquired items
                        return

                    # Find the matching location and item
                    matching_location = next(
                        loc
                        for loc in item_locations
                        if loc.item_type == item_type
                        and loc.location.lower() == self.current_location.lower()
                    )

                    # Add item to acquired items if not already there
                    if item_type not in self.acquired_items:
                        self.acquired_items.append(item_type)
                        # Remove location from global locations list
                        item_locations[:] = [
                            loc for loc in item_locations if loc != matching_location
                        ]
                        # Remove from known items if it was being sought
                        if item_type in self.known_items:
                            self.known_items.remove(item_type)
                        if self.logger:
                            self.logger.log_system_message(
                                "found",
                                f"{self.name} found the {item_type} in the {self.current_location}!",
                            )
                        else:
                            print(
                                f"\n🎉 {self.name} found the {item_type} in the {self.current_location}!"
                            )

                        # Add auto-note about finding an item
                        if self.use_notepad_instead_of_knowledge:
                            self.auto_note(
                                f"I found the {item_type} in the {self.current_location}."
                            )
                # TODO: idk, sometimes i like the idea that the agent searches say, the City, but cannot conclusively say they couldn't find it
                # else:
                #     # Add auto-note about not finding an item
                #     if self.use_notepad_instead_of_knowledge:
                #         self.auto_note(f"I searched for the {item_type.value} in the {self.current_location} but didn't find it.")

            elif action_type == "dialogue_action":
                # Extract item location information from dialogue messages
                if action.target_agent == AgentName(self.name):
                    # Process the message text for potential item location information
                    message_text = action.message.lower()
                    for item_type in ItemType:
                        item_name = item_type.value.lower()
                        if item_name in message_text:
                            # Look for location patterns like "X is in Y" or "X is at Y"
                            for location_pattern in [
                                f"{item_name} is in ",
                                f"{item_name} is at ",
                            ]:
                                if location_pattern in message_text:
                                    start_idx = message_text.find(
                                        location_pattern
                                    ) + len(location_pattern)
                                    # Extract location (simple approach - take word after pattern)
                                    potential_location = (
                                        message_text[start_idx:]
                                        .split(".")[0]
                                        .split(",")[0]
                                        .strip()
                                    )

                                    # If this is our sought item, make a note
                                    if (
                                        self.use_notepad_instead_of_knowledge
                                        and hasattr(self.motivation, "item_type")
                                    ):
                                        if self.motivation.item_type == item_type:
                                            self.auto_note(
                                                f"I learned from {agent.name} that the {item_type.value} is in {potential_location}."
                                            )

                # Regular knowledge update from dialogue
                new_knowledge = action.knowledge
                if new_knowledge:
                    # Handle string knowledge
                    if isinstance(new_knowledge, str):
                        if self.logger:
                            self.logger.log_system_message(
                                "knowledge", f"{self.name} learned: {new_knowledge}"
                            )
                        else:
                            print(f"\n💡 {self.name} learned: {new_knowledge}")

                        # Add auto-note for general knowledge
                        if self.use_notepad_instead_of_knowledge:
                            self.auto_note(
                                f"I learned from {agent.name} that {new_knowledge}"
                            )
                    # Handle Knowledge object (if not using notepad)
                    elif not self.use_notepad_instead_of_knowledge:
                        # Check for new item locations
                        for item_location in new_knowledge.item_locations:
                            item_location.location = (
                                item_location.location.lower()
                            )  # normalize case

                            # Check if we already know about this item location
                            location_exists = any(
                                k.location.lower() == item_location.location.lower()
                                and k.item_type == item_location.item_type
                                for k in self.knowledge.item_locations
                            )

                            if not location_exists:
                                self.knowledge.item_locations.append(item_location)

                                if self.logger:
                                    self.logger.log_system_message(
                                        "knowledge",
                                        f"{self.name} learned: {item_location.item_type.value} is in {item_location.location}",
                                    )
                                else:
                                    print(
                                        f"\n💡 {self.name} learned: {item_location.item_type.value} is in {item_location.location}"
                                    )

                                # Add the item type to known items if we don't have it
                                if item_location.item_type not in self.known_items:
                                    self.known_items.append(item_location.item_type)

                        # Update known places
                        new_locations = new_knowledge.places - self.known_locations
                        if new_locations:
                            self.known_locations.update(new_locations)
                            if self.logger:
                                for place in new_locations:
                                    self.logger.log_system_message(
                                        "location",
                                        f"{self.name} discovered new location: {place}",
                                    )
                            else:
                                for place in new_locations:
                                    print(
                                        f"\n🗺️  {self.name} discovered new location: {place}"
                                    )

                        # Update known agents
                        for new_agent in new_knowledge.agents:
                            if (
                                new_agent != self.name
                                and new_agent not in self.known_agents
                            ):
                                self.known_agents.append(new_agent)
                                if self.logger:
                                    self.logger.log_system_message(
                                        "meeting",
                                        f"{self.name} learned about agent: {new_agent}",
                                    )
                                else:
                                    print(
                                        f"\n🤝 {self.name} learned about agent: {new_agent}"
                                    )

                        # track items mentioned in questions
                        if action.is_question and action.knowledge_desired:
                            knowledge_desired = action.knowledge_desired
                            if knowledge_desired not in self.known_items:
                                self.known_items.append(knowledge_desired)

            elif action_type == "travel_action":
                # learn about new locations from observing travel
                new_location = action.location
                if new_location not in self.known_locations:
                    self.known_locations.add(new_location)
                    if self.logger:
                        self.logger.log_system_message(
                            "location",
                            f"{self.name} discovered new location: {new_location}",
                        )
                    else:
                        print(
                            f"\n🗺️  {self.name} discovered new location: {new_location}"
                        )

                    # Add auto-note about new locations
                    if self.use_notepad_instead_of_knowledge:
                        self.auto_note(
                            f"I discovered a new place called {new_location}."
                        )

                # update current_location if this is our own travel action
                if agent.name == self.name:
                    old_location = self.current_location
                    self.current_location = new_location

                    # Add auto-note about travel
                    if self.use_notepad_instead_of_knowledge:
                        self.auto_note(
                            f"I traveled from {old_location} to {new_location}."
                        )

            elif action_type == "notepad_action":
                # Process notepad action (only for the agent taking the action)
                if agent.name == self.name:
                    self.notes.append(action.note)
                    if self.logger:
                        self.logger.log_system_message(
                            "notepad", f"{self.name} made a note: {action.note}"
                        )
                    else:
                        print(f"\n📝 {self.name} made a note: {action.note}")

            elif action_type == "give_action":
                if (
                    action.target_agent == AgentName(self.name)
                    and agent.name != self.name
                ):
                    # This agent is receiving an item
                    item_type = action.item_type

                    # Check if giving agent has the item
                    if item_type in agent.acquired_items:
                        # Add item to this agent's inventory
                        if item_type not in self.acquired_items:
                            self.acquired_items.append(item_type)

                            # Remove from giving agent's inventory
                            agent.acquired_items.remove(item_type)

                            if self.logger:
                                self.logger.log_system_message(
                                    "give",
                                    f"{agent.name} gave {item_type} to {self.name}",
                                )
                            else:
                                print(
                                    f"\n🎁 {agent.name} gave {item_type} to {self.name}"
                                )

                            # Add auto-note about receiving an item
                            if self.use_notepad_instead_of_knowledge:
                                self.auto_note(
                                    f"I received the {item_type} from {agent.name}."
                                )

                            # If this is the item the agent was seeking, make a special note
                            if (
                                hasattr(self.motivation, "item_type")
                                and self.motivation.item_type == item_type
                            ):
                                if self.use_notepad_instead_of_knowledge:
                                    self.auto_note(
                                        f"I have successfully obtained the {item_type} I was seeking!"
                                    )

                # If this is our action (we are giving an item)
                elif agent.name == self.name:
                    item_type = action.item_type
                    receiver = action.target_agent

                    # Add auto-note about giving an item
                    if self.use_notepad_instead_of_knowledge:
                        self.auto_note(f"I gave the {item_type} to {receiver}.")

        except Exception as e:
            import traceback

            traceback.print_exc()
            # from pdb import set_trace; set_trace()

            print(f"\n❌ Error processing action for {self.name}: {e}")

    def print_state(self):
        """Print the current state of the agent"""
        print(f"\n📊 {self.name}'s Current State:")
        print(f"   📍 Location: {self.current_location}")

        if self.acquired_items:
            print(
                f"   🎒 Inventory: {', '.join(item.value for item in self.acquired_items)}"
            )

        if isinstance(self.motivation, SeekMotivation):
            print(f"   🎯 Seeking: {self.motivation.item_type.value}")
        else:
            print(f"   🤝 Motivation: {self.motivation.motivation_name}")

        if self.use_notepad_instead_of_knowledge:
            print("   📝 Notes (Memory):")
            for note in self.notes:
                print(f"      • {note}")
        else:
            # Combine all knowledge into one section
            print("   💡 Knowledge:")
            # Print item locations
            for k in self.knowledge.item_locations:
                print(f"      • Item: {k.item_type.value} is in {k.location.value}")
            # Print known locations
            if self.known_locations:
                print(f"      • Places: {', '.join(sorted(self.known_locations))}")
            # Print known agents
            if self.known_agents:
                print(f"      • Agents: {', '.join(sorted(self.known_agents))}")

    @staticmethod
    def format_available_actions() -> str:
        """Format the list of available actions"""
        actions = [
            DialogueAction,
            TravelAction,
            SearchAction,
            NotepadAction,
            GiveAction,
        ]
        return "Available Actions:\n\n" + "\n\n".join(
            f"{i + 1}. {action.format_spec()}" for i, action in enumerate(actions)
        )

    def auto_note(self, note_text: str) -> None:
        """Automatically add a note to the agent's notepad with proper logging."""
        if note_text not in self.notes:  # Avoid duplicate notes
            self.notes.append(note_text)
            if self.logger:
                self.logger.log_system_message(
                    "notepad", f"{self.name} automatically noted: {note_text}"
                )
            else:
                print(f"\n📝 Auto-note for {self.name}: {note_text}")


class Supervisor:
    def validate_action(
        self, agent: Agent, action: BaseAction, global_past_actions: list
    ) -> tuple[bool, str]:
        """
        Uses LLM to validate if an action is logically consistent with the current world state.

        Returns:
            tuple[bool, str]: (is_valid, reason)
        """
        # Extract recent history for context
        recent_history = global_past_actions[-5:] if global_past_actions else []

        prompt = f"""As a world supervisor, evaluate if this action is logically consistent for the agent to perform.

IMPORTANT: Each agent has their own knowledge, goals, and perspective. An action should be evaluated ONLY based on whether it's consistent with THIS specific agent's knowledge and state - not what other agents know or have done.

CURRENT WORLD STATE:
Agent Name: {agent.name}
Current Location: {agent.current_location}
Motivation: {agent.motivation.motivation_name}
{"Item Seeking: " + agent.motivation.item_type.value if hasattr(agent.motivation, "item_type") else ""}
Known Items: {[item.value for item in agent.known_items]}
Known Locations: {list(agent.known_locations)}
Known Agents: {agent.known_agents}
Acquired Items: {[item for item in agent.acquired_items]}
Notes: {agent.notes}

PROPOSED ACTION:
Type: {action.type}
{"Message: " + action.message if hasattr(action, "message") else ""}
{"Location: " + action.location if hasattr(action, "location") else ""}
{"Item Type: " + action.item_type if hasattr(action, "item_type") else ""}
{"Target Agent: " + action.target_agent or "" if hasattr(action, "target_agent") else ""}

RECENT HISTORY:
{recent_history}

TASK:
Analyze if this action is logically consistent with THIS SPECIFIC AGENT'S current state and knowledge.
Consider:
1. Is this action physically possible given the agent's current location and known information?
2. Is this action aligned with the agent's motivation and goals?
3. Does the action make logical sense as a next step from the agent's perspective?
4. Is there a clear logical inconsistency between what THIS AGENT knows and what they're trying to do?
5. Would THIS AGENT with their unique knowledge and goals choose this action?

IMPORTANT NOTES:
- Different agents may have different knowledge about the same objects
- Actions by other agents are not necessarily relevant to what this agent should do
- Agent A might believe an item is in Location X while Agent B believes it's in Location Y
- Both agents acting according to their beliefs is valid, even if one is incorrect
- The validation should focus ONLY on internal consistency of this agent's beliefs and actions

Respond with a JSON object:
{{
    "is_valid": true/false,
    "reason": "Detailed explanation of why the action is valid or invalid"
}}

NOTE: An action should be considered invalid ONLY if there is a clear logical inconsistency within THIS AGENT'S own knowledge and goals. If the action is simply suboptimal but still makes logical sense for this agent, consider it valid.
"""

        response = _llm_service.chat(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format=ValidationResult.model_json_schema(),
        )

        try:
            result = ValidationResult.model_validate_json(
                response["message"]["content"]
            )
            return result.is_valid, result.reason
        except Exception as e:
            return False, f"Error parsing supervisor response: {str(e)}"


class NoteExtraction(BaseModel):
    """Model for memory extraction results."""

    note: str


# Base class with common fields
class BaseMemoryAction(BaseModel):
    """Base class for memory actions"""

    reason: str = Field(..., min_length=1)
    confidence: int = Field(default=0, ge=0, le=100)


# Specific action type models
class AddMemoryAction(BaseMemoryAction):
    """Add a new note"""

    action_type: Literal["add"] = "add"
    new_content: str = Field(..., min_length=1)


class ReviseMemoryAction(BaseMemoryAction):
    """Revise existing notes"""

    action_type: Literal["revise"] = "revise"
    target_notes: List[int] = Field(..., min_items=1)
    new_content: str = Field(..., min_length=1)


class DeleteMemoryAction(BaseMemoryAction):
    """Delete existing notes"""

    action_type: Literal["delete"] = "delete"
    target_notes: List[int] = Field(..., min_items=1)


class NoActionMemoryAction(BaseMemoryAction):
    """No change to memory"""

    action_type: Literal["no_action"] = "no_action"


MemoryActionType = Union[
    AddMemoryAction, ReviseMemoryAction, DeleteMemoryAction, NoActionMemoryAction
]
MemoryAction = TypeAdapter(MemoryActionType)


class MemoryMinder:
    """
    A system to help agents manage their memory/notepad effectively
    """

    @staticmethod
    def manage_agent_memory(agent, action, world_state):
        """
        Updates an agent's notepad with extracted information using LLM
        Returns (success, message) tuple
        """
        if not agent.use_notepad_instead_of_knowledge:
            return False, "Agent is not using notepad mode"

        # Extract relevant contextual information
        if hasattr(agent, "motivation") and hasattr(agent.motivation, "item_type"):
            sought_item = agent.motivation.item_type.value
        else:
            sought_item = None

        # Extract information about the latest action
        latest_action_info = "No recent action"
        try:
            if action:
                # Format depends on whether this is our action or another agent's
                if isinstance(action, dict):  # Action from global_past_actions
                    agent_name = list(action.keys())[0]
                    action_obj = action[agent_name]
                    action_type = action_obj.type
                    action_details = action_obj.model_dump_json(indent=2)
                    latest_action_info = (
                        f"Action by {agent_name}: {action_type}\n{action_details}"
                    )
                else:  # Direct action object
                    action_type = action.type
                    action_details = action.model_dump_json(indent=2)
                    latest_action_info = (
                        f"Action by agent: {action_type}\n{action_details}"
                    )
        except Exception as e:
            latest_action_info = f"Error extracting action info: {str(e)}"

        # Structure the current notes with indices for easier reference
        indexed_notes = [f"[{i}] {note}" for i, note in enumerate(agent.notes)]

        prompt = f"""As a memory management assistant for agent {agent.name}, help organize their notes.

CURRENT NOTES:
{indexed_notes}

AGENT INFORMATION:
- Location: {agent.current_location}
- Motivation: {agent.motivation.motivation_name}
- Seeking Item: {sought_item if sought_item else "Not seeking any specific item"}
- Known Items: {[item.value for item in agent.known_items]}
- Acquired Items: {[item for item in agent.acquired_items]}

LATEST ACTION:
{latest_action_info}

TASK:
Analyze the existing notes and latest action to determine the best memory management action:
1. ADD a new note when there's completely new information
2. REVISE existing note(s) when you can improve/update old notes with new information
3. DELETE note(s) that are outdated, contradicted, or redundant
4. Take NO_ACTION if nothing needs to change

MEMORY ORGANIZATION PRINCIPLES:
- PRESERVE all important information, especially about {sought_item if sought_item else "any items"}
- Only delete notes that are clearly obsolete or completely redundant
- Consolidate only when information is truly duplicative
- Information about item locations is highest priority
- Notes that contain unique details should be preserved
- Notes about completed goals can be summarized
- Choose "no_action" if nothing needs to change

Respond with this JSON structure:
{{
  "action_type": "add" or "revise" or "delete" or "no_action",
  "target_notes": [list of note indices to modify] or null,
  "new_content": "New note text (for add or revise)" or null,
  "reason": "Brief explanation of your decision",
  "confidence": 0-100
}}

Example: Combine notes when they contain redundant information:
{{
  "action_type": "revise",
  "target_notes": [2, 4],
  "new_content": "The Sword is confirmed to be in the Field, according to multiple sources.",
  "reason": "Notes 2 and 4 contain identical information about the Sword location",
  "confidence": 75
}}
"""

        # Get decision from LLM
        response = _llm_service.chat(
            messages=[{"role": "user", "content": prompt}],
            format=MemoryAction.json_schema(),
        )

        memory_action = MemoryAction.validate_json(response["message"]["content"])

        # Process the memory action with new confidence threshold
        if memory_action.action_type == "no_action":
            return (
                False,
                f"No action: {memory_action.reason or 'No action needed or confidence too low'} (confidence: {memory_action.confidence})",
            )

        elif memory_action.action_type == "add":
            if memory_action.new_content:
                agent.notes.append(memory_action.new_content)
                if agent.logger:
                    agent.logger.log_system_message(
                        "notepad",
                        f"MemoryMinder added a note for {agent.name}: {memory_action.new_content}",
                    )
                else:
                    print(
                        f"\n📝 MemoryMinder added a note for {agent.name}: {memory_action.new_content}"
                    )
                return (
                    True,
                    f"Added new note: {memory_action.reason} (confidence: {memory_action.confidence})",
                )
            return (
                False,
                f"No content for add action (confidence: {memory_action.confidence})",
            )

        elif memory_action.action_type == "revise":
            if not memory_action.target_notes or not memory_action.new_content:
                return (
                    False,
                    f"Missing target notes or new content for revision (confidence: {memory_action.confidence})",
                )

            # Get indices of notes to revise
            indices = sorted(memory_action.target_notes)

            # Skip if indices are out of range
            if any(i < 0 or i >= len(agent.notes) for i in indices):
                return (
                    False,
                    f"Invalid note indices for revision (confidence: {memory_action.confidence})",
                )

            # If revising a single note, just update it
            if len(indices) == 1:
                old_note = agent.notes[indices[0]]
                agent.notes[indices[0]] = memory_action.new_content
                if agent.logger:
                    agent.logger.log_system_message(
                        "notepad",
                        f"MemoryMinder revised a note for {agent.name}. Old: '{old_note}' → New: '{memory_action.new_content}'",
                    )
                else:
                    print(f"\n📝 MemoryMinder revised a note for {agent.name}:")
                    print(f"   Old: '{old_note}'")
                    print(f"   New: '{memory_action.new_content}'")
                return (
                    True,
                    f"Revised note {indices[0]}: {memory_action.reason} (confidence: {memory_action.confidence})",
                )

            # For multiple notes, only consolidate if confidence is reasonable (>65)
            elif memory_action.confidence > 65:
                old_notes = [agent.notes[i] for i in indices]
                agent.notes[indices[0]] = memory_action.new_content

                # Delete other notes (starting from the end to avoid index shifting)
                for i in reversed(indices[1:]):
                    del agent.notes[i]

                if agent.logger:
                    agent.logger.log_system_message(
                        "notepad",
                        f"MemoryMinder consolidated notes for {agent.name}: '{memory_action.new_content}'",
                    )
                else:
                    print(f"\n📝 MemoryMinder consolidated notes for {agent.name}:")
                    print(f"   Old notes: {old_notes}")
                    print(f"   New consolidated note: '{memory_action.new_content}'")
                return (
                    True,
                    f"Consolidated notes {indices}: {memory_action.reason} (confidence: {memory_action.confidence})",
                )
            else:
                return (
                    False,
                    f"Confidence too low for consolidating multiple notes (confidence: {memory_action.confidence}, required: >65)",
                )

        elif memory_action.action_type == "delete":
            # Only allow deletion when confidence is sufficient (>75)
            if memory_action.confidence < 75:
                return (
                    False,
                    f"Confidence too low for deletion (confidence: {memory_action.confidence}, required: >75)",
                )

            if not memory_action.target_notes:
                return (
                    False,
                    f"Missing target notes for deletion (confidence: {memory_action.confidence})",
                )

            # Get indices of notes to delete
            indices = sorted(memory_action.target_notes, reverse=True)

            # Skip if indices are out of range
            if any(i < 0 or i >= len(agent.notes) for i in indices):
                return (
                    False,
                    f"Invalid note indices for deletion (confidence: {memory_action.confidence})",
                )

            # Delete the notes (starting from the end to avoid index shifting)
            deleted_notes = []
            for i in indices:
                deleted_notes.append(agent.notes[i])
                del agent.notes[i]

            if deleted_notes:
                if agent.logger:
                    agent.logger.log_system_message(
                        "notepad",
                        f"MemoryMinder deleted notes for {agent.name}: {deleted_notes}",
                    )
                else:
                    print(
                        f"\n📝 MemoryMinder deleted notes for {agent.name}: {deleted_notes}"
                    )
                return (
                    True,
                    f"Deleted notes {memory_action.target_notes}: {memory_action.reason} (confidence: {memory_action.confidence})",
                )
            else:
                return (
                    False,
                    f"No notes were deleted after safety checks (confidence: {memory_action.confidence})",
                )

        return False, f"Invalid memory action (confidence: {memory_action.confidence})"

    @staticmethod
    def update_agent_memory(agent, action, world_state):
        """
        Legacy method for backward compatibility
        Updates an agent's notepad with extracted information using LLM
        Returns True if the notepad was updated, False otherwise
        """
        result, _ = MemoryMinder.manage_agent_memory(agent, action, world_state)
        return result
