from typing import List, Optional, Union, Literal
from pydantic import TypeAdapter, ValidationError, constr, field_validator

from data import (
    ItemLocation,
    BaseAction,
    DialogueAction,
    ItemType,
    LocationName,
    TravelAction,
    SearchAction,
    SeekMotivation,
    NotepadAction,
    GiveAction,
)
from agents import Agent, MemoryMinder, Supervisor


class WorldState:
    """Encapsulates the state and logic of the simulation world"""

    def __init__(self, agents: List[Agent], item_locations: List[ItemLocation]):
        self.agents = agents
        self.item_locations = item_locations
        self.supervisor = Supervisor()
        self.global_past_actions = []
        self.action_counts = {
            "dialogue_action": 0,
            "travel_action": 0,
            "search_action": 0,
            "notepad_action": 0,
            "give_action": 0,
        }
        self.total_messages = 0

    def get_possible_actions(self, agent: Agent):
        """Get the possible actions for an agent based on their current state"""

        # Define valid action classes with current constraints
        class ValidDialogueAction(DialogueAction):
            target_agent: Literal[tuple(ka for ka in agent.known_agents)]
            message: constr(min_length=1, strip_whitespace=True)

            @field_validator("target_agent")
            @classmethod
            def validate_agent(cls, v):
                # Access agent through class attribute
                if v.lower() not in [a.lower() for a in cls.agent.known_agents]:
                    raise ValueError(f"Unknown agent: {v}")
                if v.lower() == cls.agent.name.lower():
                    raise ValueError("Cannot talk to yourself")
                return v

        class ValidTravelAction(TravelAction):
            location: str
            message: constr(min_length=1, strip_whitespace=True)

            @field_validator("location")
            @classmethod
            def validate_location(cls, v):
                # TODO: known_locations only works with knowledge, not notepad
                # if v.lower() not in [l.lower() for l in cls.agent.known_locations]:
                if v.lower() not in [l.value.lower() for l in LocationName]:
                    raise ValueError(f"Unknown location: {v}")
                return v

        class ValidSearchAction(SearchAction):
            item_type: str
            message: constr(min_length=1, strip_whitespace=True)

            @field_validator("item_type")
            @classmethod
            def validate_item_type(cls, v):
                # TODO: known_items only works with knowledge, not notepad
                # if v.lower() not in [i.lower() for i in cls.agent.known_items]:
                if v.lower() not in [i.value.lower() for i in ItemType]:
                    raise ValueError(f"Unknown item type: {v}")
                return v

        class ValidNotepadAction(NotepadAction):
            note: constr(min_length=1, strip_whitespace=True)
            message: constr(min_length=1, strip_whitespace=True)

        class ValidGiveAction(GiveAction):
            target_agent: Literal[tuple(ka for ka in agent.known_agents)]
            item_type: (
                Literal[tuple(i for i in agent.acquired_items)]
                if agent.acquired_items
                else str
            )
            message: constr(min_length=1, strip_whitespace=True)

            @field_validator("target_agent")
            @classmethod
            def validate_receiver(cls, v):
                if v.lower() not in [a.lower() for a in cls.agent.known_agents]:
                    raise ValueError(f"Unknown agent: {v}")
                if v.lower() == cls.agent.name.lower():
                    raise ValueError("Cannot give items to yourself")
                return v

            @field_validator("item_type")
            @classmethod
            def validate_item(cls, v):
                if not cls.agent.acquired_items:
                    raise ValueError("You don't have any items to give")
                if v.lower() not in [i.lower() for i in cls.agent.acquired_items]:
                    raise ValueError(f"You don't have the item: {v}")
                return v

        # Set the agent as a class attribute for validation
        ValidDialogueAction.agent = agent
        ValidTravelAction.agent = agent
        ValidSearchAction.agent = agent
        ValidNotepadAction.agent = agent
        ValidGiveAction.agent = agent

        # Create union of possible actions
        available_actions = Union[
            ValidTravelAction,
            ValidDialogueAction,
            ValidSearchAction,
            ValidNotepadAction,
            ValidGiveAction,
        ]

        return available_actions

    def process_agent_action(self, agent: Agent) -> Optional[BaseAction]:
        """Process a single action for an agent. Returns the action if successful."""
        # First, update the agent's memory based on the most recent past action
        if self.global_past_actions:
            most_recent_action = self.global_past_actions[-1]
            print(
                "\n🧠 MemoryMinder is managing agent memory based on most recent past action..."
            )

            # Get UI reference if available
            ui = None
            if (
                hasattr(agent, "logger")
                and agent.logger
                and hasattr(agent.logger, "ui")
            ):
                ui = agent.logger.ui

            # Update UI for MemoryMinder
            if ui:
                ui.stats_panel.set_memory_minder_status(agent.name, True)

            if agent.use_notepad_instead_of_knowledge:
                # Run memory management
                success, message = MemoryMinder.manage_agent_memory(
                    agent, most_recent_action, self
                )

                if not success:
                    agent.logger.log_system_message(
                        "notepad",
                        f"❌ MemoryMinder skipped memory update for {agent.name}: {message}",
                    )

            # Reset UI status
            if ui:
                ui.stats_panel.set_memory_minder_status(agent.name, False)

        available_actions = self.get_possible_actions(agent)
        # Create a TypeAdapter for validating the response
        action_adapter = TypeAdapter(available_actions)
        rejection_reason = None

        # Get UI reference if available
        ui = None
        if hasattr(agent, "logger") and agent.logger and hasattr(agent.logger, "ui"):
            ui = agent.logger.ui

        while True:  # keep trying until we get a valid action
            try:
                # Set agent to thinking state and start timer
                if ui:
                    ui.stats_panel.set_agent_thinking(agent.name, True)

                response = agent.produce_next_action(
                    available_actions, self.global_past_actions, rejection_reason
                )

                # Stop thinking timer
                if ui:
                    ui.stats_panel.set_agent_thinking(agent.name, False)

                validated_action = action_adapter.validate_json(response)

                # TODO: flag to toggle supervisor
                # check if action is logically valid
                print("\n⚖️ Supervisor is evaluating...")
                # Update UI if agent has logger with UI reference
                if ui:
                    ui.stats_panel.set_supervisor_status(
                        agent.name, "Evaluating...", is_approved=None
                    )

                # is_valid, reason = self.supervisor.validate_action(
                #     agent, validated_action, self.global_past_actions
                # )

                # if not is_valid:
                #     print(f"\n⚖️ Supervisor rejected action: {reason}")
                #     print(
                #         f"❌ Rejected action: {validated_action.model_dump_json(indent=2)}"
                #     )
                #     # Update UI with rejection
                #     if ui:
                #         ui.stats_panel.set_supervisor_status(
                #             agent.name, f"Rejected: {reason}", is_approved=False
                #         )

                #     rejection_reason = reason
                #     continue  # Try again
                # else:
                #     # Update UI with approval
                #     if ui:
                #         ui.stats_panel.set_supervisor_status(
                #             agent.name, "Approved", is_approved=True
                #         )

                self.global_past_actions.append({agent.name: validated_action})

                # Update all agents' state based on the action
                for other_agent in self.agents:
                    other_agent.receive_action(
                        validated_action, agent, self.item_locations
                    )

                # Update stats using action.type instead of class name
                self.action_counts[validated_action.type] += 1
                if validated_action.type in [
                    "dialogue_action",
                    "travel_action",
                    "search_action",
                    "notepad_action",
                    "give_action",
                ]:
                    self.total_messages += 1

                # Update the final memory management call
                print(
                    "\n🧠 MemoryMinder is managing agent memory based on their own action..."
                )
                if ui:
                    ui.stats_panel.set_memory_minder_status(agent.name, True)

                if agent.use_notepad_instead_of_knowledge:
                    success, message = MemoryMinder.manage_agent_memory(
                        agent, {agent.name: validated_action}, self
                    )

                    if not success:
                        agent.logger.log_system_message(
                            "notepad",
                            f"❌ MemoryMinder skipped memory update for {agent.name}: {message}",
                        )

                if ui:
                    ui.stats_panel.set_memory_minder_status(agent.name, False)

                return validated_action

            except ValidationError as e:
                print(f"\n❌ ValidationError: {str(e)}")
                print(f"Rejected action: {response}")
                # Update UI for validation error
                if ui:
                    ui.stats_panel.set_supervisor_status(
                        agent.name, f"Validation Error: {str(e)}", is_approved=False
                    )
                continue

            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                # Update UI for other errors
                if ui:
                    ui.stats_panel.set_supervisor_status(
                        agent.name, f"Error: {str(e)}", is_approved=False
                    )

                import traceback

                traceback.print_exc()
                # from pdb import set_trace; set_trace()

                continue

    def check_victory_condition(self) -> bool:
        """Check if a seeking agent has found their item"""
        for agent in self.agents:
            if isinstance(agent.motivation, SeekMotivation):
                sought_item_type = agent.motivation.item_type.value
                if sought_item_type in agent.acquired_items:
                    return True
        return False

    def get_stats(self) -> dict:
        """Get current simulation statistics"""
        return {
            "action_counts": self.action_counts,
            "total_messages": self.total_messages,
        }
