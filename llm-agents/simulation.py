from datetime import datetime
from typing import List, Tuple
import time
import threading
import random

from agents import Agent
from data import (
    AgentName,
    BaseAction,
    ItemLocation,
    ItemType,
    LocationName,
    Knowledge,
    SeekMotivation,
    BeHelpfulMotivation,
)
from logger import Logger
from state import WorldState


def create_default_agents() -> List[Agent]:
    """Create and return the default agents for the simulation."""
    seeker_agent = Agent(
        name=AgentName.SEEKER,
        current_location=LocationName.CITY,
        known_items=[ItemType.STONE, ItemType.SWORD],
        known_locations={LocationName.CITY},
        known_agents=[AgentName.KNOWER],
        motivation=SeekMotivation(item_type=ItemType.SWORD),
        knowledge=Knowledge(),
    )

    knower_agent = Agent(
        name=AgentName.KNOWER,
        current_location=LocationName.CITY,
        known_items=[ItemType.SWORD],
        known_locations={LocationName.CITY, LocationName.FIELD},
        known_agents=[AgentName.SEEKER],
        motivation=BeHelpfulMotivation(),
        knowledge=Knowledge(
            item_locations=[
                ItemLocation(item_type=ItemType.SWORD, location=LocationName.FIELD)
            ]
        ),
    )

    return [seeker_agent, knower_agent]


def create_default_item_locations() -> List[ItemLocation]:
    """Create and return the default item locations for the simulation."""
    return [
        ItemLocation(item_type=ItemType.STONE, location=LocationName.CITY),
        ItemLocation(item_type=ItemType.SWORD, location=LocationName.FIELD),
    ]


def setup_basic_simulation(
    use_notepad_mode: bool = False,
) -> Tuple[List[Agent], List[ItemLocation]]:
    """Set up a basic simulation with two agents and locations."""
    # Set up item locations
    item_locations = [
        ItemLocation(item_type=ItemType.SWORD, location=LocationName.FIELD),
        ItemLocation(item_type=ItemType.STONE, location=LocationName.CITY),
    ]

    # Define the agents
    agents = []

    # Create a seeking agent
    seeker = Agent(
        name=AgentName.SEEKER.value,
        current_location=LocationName.CITY.value,
        known_items=[ItemType.SWORD],
        known_locations={LocationName.CITY.value, LocationName.FIELD.value},
        known_agents=[AgentName.KNOWER.value],
        motivation=SeekMotivation(item_type=ItemType.SWORD),
        use_notepad_instead_of_knowledge=use_notepad_mode,
    )

    # Create a knowledge-sharing agent
    knower = Agent(
        name=AgentName.KNOWER.value,
        current_location=LocationName.CITY.value,
        known_items=[ItemType.SWORD, ItemType.STONE],
        known_locations={LocationName.CITY.value, LocationName.FIELD.value},
        known_agents=[AgentName.SEEKER.value],
        motivation=BeHelpfulMotivation(),
        use_notepad_instead_of_knowledge=use_notepad_mode,
    )

    # Add knowledge about item locations
    knower.knowledge.item_locations.append(
        ItemLocation(item_type=ItemType.SWORD, location=LocationName.FIELD)
    )
    knower.knowledge.item_locations.append(
        ItemLocation(item_type=ItemType.STONE, location=LocationName.CITY)
    )

    # Initialize the notepad with knowledge if in notepad mode
    if use_notepad_mode:
        seeker.initialize_notepad()
        knower.initialize_notepad()

    agents.extend([seeker, knower])

    return agents, item_locations


def setup_complex_simulation(
    use_notepad_mode: bool = False,
) -> Tuple[List[Agent], List[ItemLocation]]:
    """Set up a more complex simulation with multiple agents and locations"""
    # Define item locations
    item_locations = [
        ItemLocation(item_type=ItemType.SWORD, location=LocationName.CAVE),
        ItemLocation(item_type=ItemType.STONE, location=LocationName.FOREST),
        ItemLocation(item_type=ItemType.KEY, location=LocationName.MOUNTAIN),
        ItemLocation(item_type=ItemType.TREASURE, location=LocationName.BEACH),
    ]

    # Create agents
    agents = []

    # Seeker - Looking for the Treasure
    seeker = Agent(
        name="Seeker",
        current_location="City",
        known_items=[ItemType.TREASURE],
        known_locations={"City", "Field"},
        known_agents=["Guide", "Wanderer"],
        motivation=SeekMotivation(item_type=ItemType.TREASURE),
        use_notepad_instead_of_knowledge=use_notepad_mode,
    )

    # Guide - Knows about some locations but has partial information
    guide = Agent(
        name="Guide",
        current_location="City",
        known_items=[ItemType.KEY, ItemType.TREASURE],
        known_locations={"City", "Field", "Forest", "Mountain"},
        known_agents=["Seeker", "Wanderer"],
        motivation=BeHelpfulMotivation(),
        use_notepad_instead_of_knowledge=use_notepad_mode,
    )

    # Explorer - Knows about caves and where the Sword is
    explorer = Agent(
        name="Explorer",
        current_location="Field",
        known_items=[ItemType.SWORD, ItemType.KEY],
        known_locations={"City", "Field", "Cave"},
        known_agents=["Guide"],
        motivation=BeHelpfulMotivation(),
        use_notepad_instead_of_knowledge=use_notepad_mode,
    )

    # Wanderer - Knows about the beach and treasure, but is in a remote location
    wanderer = Agent(
        name="Wanderer",
        current_location="Forest",
        known_items=[ItemType.TREASURE, ItemType.STONE],
        known_locations={"Forest", "Beach"},
        known_agents=["Seeker", "Guide"],
        motivation=BeHelpfulMotivation(),
        use_notepad_instead_of_knowledge=use_notepad_mode,
    )

    # Add knowledge to each agent
    # Guide knows where the Key is and that the Treasure requires a Key
    guide.knowledge.item_locations.append(
        ItemLocation(item_type=ItemType.KEY, location=LocationName.MOUNTAIN)
    )

    # Explorer knows where the Sword is
    explorer.knowledge.item_locations.append(
        ItemLocation(item_type=ItemType.SWORD, location=LocationName.CAVE)
    )

    # Wanderer knows where the Stone and Treasure are
    wanderer.knowledge.item_locations.append(
        ItemLocation(item_type=ItemType.STONE, location=LocationName.FOREST)
    )
    wanderer.knowledge.item_locations.append(
        ItemLocation(item_type=ItemType.TREASURE, location=LocationName.BEACH)
    )

    # Initialize notepads if in notepad mode
    if use_notepad_mode:
        seeker.initialize_notepad()
        guide.initialize_notepad()
        explorer.initialize_notepad()
        wanderer.initialize_notepad()

    # Add agents to list
    agents.extend([seeker, guide, explorer, wanderer])

    return agents, item_locations


def setup_simulation(use_notepad_mode: bool = False, use_complex: bool = True):
    """
    Set up the simulation, determining if we should use the basic or complex setup.

    Args:
        use_notepad_mode: Whether to use notepad instead of knowledge
        use_complex: Whether to use the complex simulation (default) or basic simulation

    Returns:
        Tuple of (agents, item_locations)
    """
    if use_complex:
        return setup_complex_simulation(use_notepad_mode)
    else:
        return setup_basic_simulation(use_notepad_mode)


class TurnManager:
    """Manages agent turn selection using different strategies."""

    def __init__(self, agents, strategy="round_robin"):
        """
        Initialize the turn manager.

        Args:
            agents: List of agents to manage
            strategy: Turn selection strategy (round_robin, priority, reactive, location)
        """
        self.agents = agents
        self.strategy = strategy
        self.current_index = 0
        self.last_action = None
        self.action_counts = {agent.name: 0 for agent in agents}
        self.logger = None  # Will be set by WorldSimulation

    def next_agent(self, world_state=None):
        """
        Get the next agent to take a turn based on the selected strategy.

        Args:
            world_state: Optional WorldState object for strategies that need context

        Returns:
            The next Agent to take a turn
        """
        selected_agent = None
        selected_strategy = self.strategy

        if self.strategy == "round_robin":
            selected_agent = self._round_robin_strategy()
        elif self.strategy == "priority":
            selected_agent = self._priority_strategy(world_state)
        elif self.strategy == "reactive":
            selected_agent = self._reactive_strategy(world_state)
        elif self.strategy == "location":
            selected_agent = self._location_based_strategy(world_state)
        elif self.strategy == "balanced":
            selected_agent, selected_strategy = self._balanced_strategy(world_state)
        else:
            # Default to round robin
            selected_agent = self._round_robin_strategy()
            selected_strategy = "round_robin"

        # Log which strategy was used
        if self.logger:
            self.logger.log_system_message(
                "turn",
                f"➡️ Turn manager selected {selected_agent.name} using '{selected_strategy}' strategy",
            )

        return selected_agent

    def update_after_action(self, agent, action):
        """Update manager state after an action is taken."""
        self.last_action = {"agent": agent, "action": action}
        self.action_counts[agent.name] += 1

    def _round_robin_strategy(self):
        """Simple round-robin turn selection (the current implementation)."""
        agent = self.agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.agents)
        return agent

    def _priority_strategy(self, world_state):
        """
        Select based on agent priority.
        - Seeking agents get higher priority when they're close to their goal
        - Agents with information needed by others get higher priority
        """
        # Get priorities for all agents
        priorities = []
        priority_explanations = {}

        for agent in self.agents:
            priority = 1.0  # Base priority
            explanation = ["Base priority: 1.0"]

            # Priority boost for seekers who know where their item is
            if hasattr(agent.motivation, "item_type"):
                sought_item = agent.motivation.item_type
                explanation.append(f"Seeking {sought_item.value}")

                # Check if agent knows where their item is
                for loc in agent.knowledge.item_locations:
                    if loc.item_type == sought_item:
                        # Higher priority if they know where their item is
                        priority += 2.0
                        explanation.append(
                            f"+2.0: Knows {sought_item.value} location ({loc.location.value})"
                        )

                        # Even higher if they're in that location
                        if loc.location.value.lower() == agent.current_location.lower():
                            priority += 3.0
                            explanation.append(
                                "+3.0: Currently at sought item location"
                            )

            # Knowledge-sharing agents get priority when others need information
            if not hasattr(agent.motivation, "item_type"):  # Helper agents
                explanation.append("Helper agent")

                # Check if other agents need information this agent has
                for other_agent in self.agents:
                    if other_agent != agent and hasattr(
                        other_agent.motivation, "item_type"
                    ):
                        sought_item = other_agent.motivation.item_type
                        # This agent knows about an item another agent seeks
                        for loc in agent.knowledge.item_locations:
                            if loc.item_type == sought_item:
                                priority += 1.5
                                explanation.append(
                                    f"+1.5: Has info about {sought_item.value} that {other_agent.name} seeks"
                                )

                                # Even higher if they're in the same location
                                if (
                                    agent.current_location
                                    == other_agent.current_location
                                ):
                                    priority += 1.0
                                    explanation.append(
                                        f"+1.0: In same location as {other_agent.name}"
                                    )

            # Balance based on previous action count
            action_count = self.action_counts.get(agent.name, 0)
            decay_factor = 0.9**action_count
            old_priority = priority
            priority = priority * decay_factor
            explanation.append(
                f"×{decay_factor:.2f}: Action count balance ({action_count} previous actions)"
            )
            explanation.append(f"Final score: {priority:.2f}")

            priorities.append((agent, priority))
            priority_explanations[agent.name] = explanation

        # Sort by priority (highest first) and return the highest priority agent
        priorities.sort(key=lambda x: x[1], reverse=True)
        selected_agent = priorities[0][0]

        # Log the priority calculations
        if self.logger:
            log_message = "Priority scores:\n"
            for agent, score in sorted(priorities, key=lambda x: x[1], reverse=True):
                log_message += f"• {agent.name}: {score:.2f}\n"
                for line in priority_explanations[agent.name]:
                    log_message += f"  - {line}\n"

            self.logger.log_system_message("priority", log_message)

        return selected_agent

    def _reactive_strategy(self, world_state):
        """
        Select based on who should react to the previous action.
        If an agent was addressed in dialogue, they get priority to respond.
        """
        if self.last_action and self.last_action["action"].type == "dialogue_action":
            # Get the target of the last dialogue
            target_name = self.last_action["action"].target_agent

            # Find the agent with that name
            for agent in self.agents:
                if agent.name == target_name:
                    return agent

        # If no dialogue or target not found, use round robin
        return self._round_robin_strategy()

    def _location_based_strategy(self, world_state):
        """
        Prioritize agents in the same location to simulate local interaction.
        If the last agent to act was at location X, prioritize other agents at X.
        """
        if self.last_action:
            last_location = self.last_action["agent"].current_location

            # Filter agents in the same location (excluding the last agent)
            local_agents = [
                a
                for a in self.agents
                if a.current_location == last_location
                and a.name != self.last_action["agent"].name
            ]

            if local_agents:
                return local_agents[0]

        # If no agents in same location or no last action, use round robin
        return self._round_robin_strategy()

    def _balanced_strategy(self, world_state):
        """
        Balanced approach that combines aspects of multiple strategies.
        """
        # With 40% chance, use priority-based
        # With 30% chance, use reactive
        # With 20% chance, use location-based
        # With 10% chance, use round-robin

        choice = random.random()

        if choice < 0.4:
            return self._priority_strategy(world_state), "priority"
        elif choice < 0.7:
            return self._reactive_strategy(world_state), "reactive"
        elif choice < 0.9:
            return self._location_based_strategy(world_state), "location"
        else:
            return self._round_robin_strategy(), "round_robin"


class WorldSimulation:
    """
    Simulation manager that works with or without a UI.
    """

    def __init__(
        self,
        agents: List[Agent],
        item_locations: List[ItemLocation],
        ui=None,
        turn_strategy="round_robin",
    ):
        """
        Initialize the simulation.

        Args:
            agents: List of agents in the simulation
            item_locations: List of item locations in the simulation
            ui: Optional UI object to update (if None, runs in console mode)
            turn_strategy: Strategy for determining agent turn order
        """
        self.world_state = WorldState(agents, item_locations)
        self.ui = ui
        self.running = False
        self.start_time = datetime.now()
        self.logger = Logger(ui)
        self.turn_manager = TurnManager(agents, strategy=turn_strategy)

        # Connect the logger to the turn manager
        self.turn_manager.logger = self.logger

        # Assign logger to each agent
        for agent in self.world_state.agents:
            agent.logger = self.logger

        # Print welcome message
        self.logger.log_system_message("system", "🌍 Simulation started.")
        self.logger.log_system_message(
            "system", f"🔄 Using turn strategy: {turn_strategy}"
        )

        # Update UI state if UI exists
        if self.ui:
            self._update_ui_state()

    def start(self, threaded=True, delay_between_actions=10.0):
        """
        Start the simulation.

        Args:
            threaded: Whether to run in a separate thread
            delay_between_actions: Delay between actions in seconds
        """
        self.running = True
        self.start_time = datetime.now()

        if threaded:
            thread = threading.Thread(
                target=self._run_simulation, args=(delay_between_actions,), daemon=True
            )
            thread.start()
        else:
            self._run_simulation(delay_between_actions)

    def stop(self):
        """Stop the simulation."""
        self.running = False

    def _run_simulation(self, delay_between_actions=0.0):
        """
        Run the simulation loop.

        Args:
            delay_between_actions: Delay between actions in seconds
        """
        while self.running:
            # Get the next agent according to the turn strategy
            agent = self.turn_manager.next_agent(self.world_state)

            if not self.running:
                break

            # Show thinking status if UI exists
            if self.ui:
                self.ui.after(
                    0, self.ui.stats_panel.set_agent_thinking, agent.name, True
                )

            # Process agent's action
            validated_action = self.world_state.process_agent_action(agent)

            # Clear thinking status if UI exists
            if self.ui:
                self.ui.after(
                    0, self.ui.stats_panel.set_agent_thinking, agent.name, False
                )

            if validated_action:
                # Update the turn manager with the action that was taken
                self.turn_manager.update_after_action(agent, validated_action)

                # Log action effects
                self.logger.log_action(agent, validated_action)

                # Check for special events
                self._check_special_events(agent, validated_action)

                # Update UI if it exists
                if self.ui:
                    self._update_ui_state()
                    stats = self.world_state.get_stats()
                    self._update_stats(stats)

            # Small delay between actions
            if delay_between_actions > 0:
                time.sleep(delay_between_actions)

            if self.world_state.check_victory_condition():
                self._handle_victory()
                self.running = False
                break

    def _check_special_events(self, agent: Agent, action: BaseAction):
        """
        Check for special events that need to be logged.

        Args:
            agent: The agent performing the action
            action: The action being performed
        """
        action_type = action.type

        if action_type == "dialogue_action":
            target = action.target_agent
            # Log agent meetings
            if target not in agent.known_agents and target != agent.name:
                self.logger.log_system_message("meeting", f"{agent.name} met {target}")

        elif action_type == "travel_action":
            target = action.location
            # Log location discoveries
            for observing_agent in self.world_state.agents:
                if target not in observing_agent.known_locations:
                    self.logger.log_system_message(
                        "location",
                        f"{observing_agent.name} discovered new location: {target}",
                    )

        elif action_type == "search_action":
            # Check if item was found
            location_has_item = any(
                loc.item_type == action.item_type
                and loc.location.lower() == agent.current_location.lower()
                for loc in self.world_state.item_locations
            )

            if location_has_item:
                self.logger.log_system_message(
                    "found", f"{agent.name} found the {action.item_type}!"
                )

    def _handle_victory(self):
        """Handle victory condition and display final stats."""
        duration = (datetime.now() - self.start_time).total_seconds()
        stats = self.world_state.get_stats()

        # Log victory only if UI isn't handling it
        if not self.ui:
            self.logger.log_victory(duration, stats)
            # Explicitly stop the simulation in console mode
            self.running = False
        else:
            # Let the UI handle both stopping and logging
            self.ui.on_victory()

    def _update_ui_state(self):
        """Update UI with current simulation state. Only called if UI exists."""
        if not self.ui:
            return

        # Update locations
        locations = {}

        # First, initialize all locations with empty sets
        for location_name in LocationName:
            locations[location_name.value] = {"agents": set(), "items": set()}

        # Then populate with current agent locations
        for agent in self.world_state.agents:
            locations[agent.current_location]["agents"].add(agent.name)

        # Add items to locations
        for loc in self.world_state.item_locations:
            location = loc.location.value
            item = loc.item_type.value
            locations[location]["items"].add(item)

        # Update ALL locations in UI grid, not just populated ones
        for location, contents in locations.items():
            self.ui.world_grid.update_location(
                location, contents["agents"], contents["items"]
            )

        # Update agent stats
        for agent in self.world_state.agents:
            knowledge_parts = []

            if agent.knowledge.item_locations:
                items = [
                    f"{k.item_type.value} → {k.location}"
                    for k in agent.knowledge.item_locations
                ]
                knowledge_parts.append(f"  Items: {', '.join(items)}")

            if agent.known_locations:
                knowledge_parts.append(
                    f"  Places: {', '.join(sorted(agent.known_locations))}"
                )

            if agent.known_agents:
                knowledge_parts.append(
                    f"  Agents: {', '.join(sorted(agent.known_agents))}"
                )

            knowledge_str = "\n".join(knowledge_parts) if knowledge_parts else "none"

            motivation_str = agent.motivation.motivation_name
            if hasattr(agent.motivation, "item_type"):
                motivation_str += f" → {agent.motivation.item_type.value}"

            self.ui.stats_panel.update_agent(
                name=agent.name,
                location=agent.current_location,
                inventory=agent.acquired_items,
                motivation=motivation_str,
                knowledge=knowledge_str,
                notes=agent.notes,
                show_knowledge=not agent.use_notepad_instead_of_knowledge,
            )

    def _update_stats(self, stats: dict):
        """Update statistics based on new stats. Only called if UI exists."""
        if not self.ui:
            return

        self.ui.stats_panel.update_time((datetime.now() - self.start_time).seconds)
        self.ui.stats_panel.update_action_counts(stats["action_counts"])
