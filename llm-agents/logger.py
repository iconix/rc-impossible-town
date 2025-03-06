from typing import Any, Dict

from agents import Agent
from data import BaseAction, ACTION_ICONS


class Logger:
    """A configurable logger that can output to console or UI."""

    def __init__(self, ui=None):
        """
        Initialize the logger.

        Args:
            ui: Optional WorldUI object to update
        """
        self.ui = ui
        self.icons = ACTION_ICONS  # Use centralized icons

    def _output(
        self, message: str, msg_type: str = "system", output_to_ui: bool = False
    ):
        """
        Output a message to both console and UI.

        Args:
            message: The message to output
            msg_type: The type of message for UI categorization
        """
        # Always print to console (with icon)
        print(message)

        # If UI exists, also send to UI (without icon if it's at the beginning)
        if self.ui and message.strip() and output_to_ui:
            # Strip icon from the beginning if present to avoid duplication
            # UI will add its own icon
            for icon in self.icons.values():
                if message.startswith(icon):
                    message = message[len(icon) :]
                    break
            self.ui.action_log.add_system_message(msg_type, message)

    def log_action(self, agent: Agent, action: BaseAction):
        """Log an action with appropriate formatting."""
        # Print action details using the centralized icons
        self._output(
            f"\n{self.icons.get('action_start', '')}{agent.name}'s action:",
            "action_start",
        )

        action_type = action.type
        if action_type == "dialogue_action":
            self._output(
                f"   {self.icons.get('dialogue', '')}To {action.target_agent}: {action.message}",
                "dialogue",
            )

            # Update UI action log if UI exists
            if self.ui:
                self.ui.action_log.add_action(
                    agent.name, "dialogue", action.message, target=action.target_agent
                )

                # Highlight agents in UI
                self.ui.highlight_agent_temporarily(agent.name)
                # self.ui.highlight_agent_temporarily(action.target_agent)

            # Log knowledge sharing
            if action.knowledge:
                # Handle string knowledge
                if isinstance(action.knowledge, str):
                    self.log_system_message(
                        "knowledge", f"{agent.name} shared: {action.knowledge}"
                    )
                # Handle Knowledge object
                else:
                    for item_loc in action.knowledge.item_locations:
                        self.log_system_message(
                            "knowledge",
                            f"{agent.name} shared: {item_loc.item_type.value} is in {item_loc.location}",
                        )

                    if action.knowledge.places:
                        self.log_system_message(
                            "knowledge",
                            f"{agent.name} shared a place: {', '.join(sorted(action.knowledge.places))}",
                        )

                    if action.knowledge.agents:
                        self.log_system_message(
                            "knowledge",
                            f"{agent.name} shared an agent: {', '.join(sorted(action.knowledge.agents))}",
                        )

        elif action_type == "travel_action":
            target = action.location
            self._output(
                f"   {self.icons.get('travel', '')}Moving to: {target}", "travel"
            )
            self._output(
                f"   {self.icons.get('dialogue', '')}To {action.target_agent}: {action.message}",
                "dialogue",
            )

            # Update UI action log if UI exists
            if self.ui:
                self.ui.action_log.add_action(
                    agent.name, "travel", action.message, target=target
                )

                # Highlight location and agent in UI
                self.ui.highlight_location_temporarily(target)
                self.ui.highlight_agent_temporarily(agent.name)

        elif action_type == "search_action":
            self._output(f"   🔍 Searching for: {action.item_type}", "search")
            self._output(
                f"   💬 To {action.target_agent}: {action.message}", "dialogue"
            )

            # Update UI action log if UI exists
            if self.ui:
                self.ui.action_log.add_action(
                    agent.name, "search", action.message, target=action.item_type
                )

                # Highlight agent and location in UI
                self.ui.highlight_agent_temporarily(agent.name)
                self.ui.highlight_location_temporarily(agent.current_location)

        elif action_type == "notepad_action":
            self._output(f"   📝 Note: {action.note}", "notepad")
            self._output(
                f"   💬 To {action.target_agent}: {action.message}", "dialogue"
            )

            # Update UI action log if UI exists
            if self.ui:
                self.ui.action_log.add_action(
                    agent.name, "notepad", action.message, target=action.note
                )

                # Highlight agent in UI
                self.ui.highlight_agent_temporarily(agent.name)

        elif action_type == "give_action":
            self._output(
                f"   🎁 Giving {action.item_type} to: {action.target_agent}", "give"
            )
            self._output(
                f"   💬 To {action.target_agent}: {action.message}", "dialogue"
            )

            # Update UI action log if UI exists
            if self.ui:
                self.ui.action_log.add_action(
                    agent.name, "give", action.message, target=action.target_agent
                )

                # Highlight agent and target agent in UI
                self.ui.highlight_agent_temporarily(agent.name)
                # self.ui.highlight_agent_temporarily(action.target_agent)

        # Print agent state
        self.log_agent_state(agent)

        if action.end_turn:
            # self._output(f"\n⏱️ {agent.name}'s turn ends", "turn")
            pass
        else:
            self._output(
                f"\n{self.icons.get('turn', '')}{agent.name} continues their turn",
                "turn",
            )

    def log_agent_state(self, agent: Agent):
        """Log agent state information."""
        self._output(
            f"\n{self.icons.get('state', '')}{agent.name}'s Current State:", "state"
        )
        self._output(f"   🏠 Location: {agent.current_location}", "state")

        if agent.acquired_items:
            self._output(
                f"   🎒 Inventory: {', '.join(item for item in agent.acquired_items)}",
                "state",
            )

        # Add motivation
        if hasattr(agent.motivation, "item_type"):
            self._output(f"   🎯 Seeking: {agent.motivation.item_type.value}", "state")
        else:
            self._output(
                f"   🤝 Motivation: {agent.motivation.motivation_name}", "state"
            )

        # Show knowledge or notes based on agent mode
        if agent.use_notepad_instead_of_knowledge:
            # Display notes prominently in notepad mode
            self._output("   📝 Notes (Memory):", "state")
            if agent.notes:
                for note in agent.notes:
                    self._output(f"      • {note}", "state")
            else:
                self._output("      • No notes yet", "state")
        else:
            # Display knowledge in standard mode
            self._output("   💡 Knowledge:", "state")

            # Add item locations
            for k in agent.knowledge.item_locations:
                self._output(
                    f"      • Item: {k.item_type.value} is in {k.location}", "state"
                )

            # Add known locations
            if agent.known_locations:
                self._output(
                    f"      • Places: {', '.join(sorted(agent.known_locations))}",
                    "state",
                )

            # Add known agents
            if agent.known_agents:
                self._output(
                    f"      • Agents: {', '.join(sorted(agent.known_agents))}", "state"
                )

            # Add notes as additional information
            if agent.notes:
                self._output("   📝 Notes:", "state")
                for note in agent.notes:
                    self._output(f"      • {note}", "state")

    def log_system_message(self, msg_type: str, message: str):
        """Log a system message with appropriate formatting."""
        # Use the icon matching the message type for console output
        icon = self.icons.get(msg_type, self.icons.get("system", ""))

        # Check if message already starts with any emoji character
        # Simple heuristic: most emoji and special symbols are outside ASCII range
        has_emoji_prefix = message and ord(message[0]) > 127

        if has_emoji_prefix:
            # Message already has an emoji or special character, don't add another one
            print(message)
        else:
            # Message doesn't start with an emoji, add icon
            print(f"{icon}{message}")

        # If UI exists, send the raw message (UI will add its own icon if needed)
        if self.ui and message.strip():
            self.ui.action_log.add_system_message(msg_type, message)

    def log_victory(self, duration: float, stats: Dict[str, Any]):
        """Log victory message and stats."""
        # Log a more detailed victory message similar to what the simulation would show
        elapsed = int(duration)  # convert to integer seconds
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        time_str = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

        victory_message = (
            f"🎊 Game Over! Victory achieved in {time_str}!\n"
            f"Total actions: {sum(stats['action_counts'].values())}\n"
            f"Dialogue actions: {stats['action_counts']['dialogue_action']}\n"
            f"Travel actions: {stats['action_counts']['travel_action']}\n"
            f"Search actions: {stats['action_counts']['search_action']}\n"
            # f"Total messages: {stats['total_messages']}"
        )

        self._output(victory_message, "system", output_to_ui=True)
