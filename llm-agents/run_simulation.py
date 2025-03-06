import time
import argparse
import sys

from agents import configure_llm
from simulation import WorldSimulation, setup_simulation
from world_ui import WorldUI


def run_console_test_mode(use_notepad_mode=False):
    """Run a test simulation in console mode"""
    print("\n--- RUNNING TEST MODE IN CONSOLE ---")
    print("This is a pre-scripted demo showing sample agent interactions\n")

    # Import logger here to ensure we're using the same logging mechanism
    from logger import Logger
    from data import (
        DialogueAction,
        TravelAction,
        SearchAction,
        LocationName,
        ItemType,
        Knowledge,
    )

    # Track start time for victory calculation
    start_time = time.time()

    # Create a logger without UI attachment
    logger = Logger(ui=None)

    # Log system message like in real simulation
    logger.log_system_message("system", "🌍 Simulation started.")

    # Set up test locations and entities
    print("Setting up test environment:")
    print("- City: Contains Seeker, Knower, and the Stone")
    print("- Field: Contains the Sword")
    print("------------------------\n")

    # Class to mock an agent for logging
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.current_location = "City"  # Default location
            self.acquired_items = []  # Empty inventory

            # Create a simple motivation object
            class MockMotivation:
                def __init__(self):
                    self.motivation_name = "Seek"
                    self.item_type = ItemType.SWORD

            self.motivation = MockMotivation()
            self.use_notepad_instead_of_knowledge = use_notepad_mode  # Use CLI arg
            self.knowledge = Knowledge()  # Empty knowledge
            self.known_locations = {"City", "Field"}
            self.known_agents = ["Seeker", "Knower"]
            self.notes = (
                ["Look for the sword", "Ask Knower for help"]
                if use_notepad_mode
                else []
            )  # Add sample notes in notepad mode

    # Define a sequence of sample actions (similar to UI test mode)
    sample_actions = [
        (
            1,
            "Seeker",
            DialogueAction(
                target_agent="Knower",
                message="Do you know where the Sword is?",
                is_question=True,
            ),
        ),
        (
            2,
            "Knower",
            DialogueAction(
                target_agent="Seeker",
                message="Yes, it's in the field!",
                is_question=False,
            ),
        ),
        (
            3,
            "Seeker",
            TravelAction(
                target_agent="Seeker",
                location=LocationName.FIELD,
                message="I must find the sword!",
            ),
        ),
        (
            4,
            "Seeker",
            SearchAction(
                target_agent="Seeker", item_type="Sword", message="Looking carefully..."
            ),
        ),
        (5, "Seeker", "found_item", "Sword"),
    ]

    try:
        # Execute sample actions with appropriate delays
        for idx, (delay, agent_name, action, *extra) in enumerate(sample_actions):
            # Add a delay between actions
            if idx > 0:
                print(f"\n[Waiting {delay} seconds...]\n")
                time.sleep(delay)

            # Create mock agent
            agent = MockAgent(agent_name)

            # Handle special case for found_item, which isn't a real action
            if isinstance(action, str) and action == "found_item":
                item = extra[0]
                logger.log_system_message("found", f"{agent_name} found the {item}!")
            else:
                # For regular actions, use actual logger to log the action
                if isinstance(action, TravelAction):
                    agent.current_location = (
                        action.location.value
                    )  # Update agent location with enum value

                logger.log_action(agent, action)

        # Calculate duration
        duration = time.time() - start_time

        # Create a stats dictionary for the victory message
        # Count each action type
        action_counts = {
            "dialogue_action": sum(
                1 for _, _, a, *_ in sample_actions if isinstance(a, DialogueAction)
            ),
            "travel_action": sum(
                1 for _, _, a, *_ in sample_actions if isinstance(a, TravelAction)
            ),
            "search_action": sum(
                1 for _, _, a, *_ in sample_actions if isinstance(a, SearchAction)
            ),
            "give_action": 0,
            "notepad_action": 0,
        }

        stats = {"action_counts": action_counts}

        # Log the victory
        logger.log_victory(duration, stats)

        print("\n--- TEST SIMULATION COMPLETE ---")
        print("In a real simulation, agents would make decisions using LLMs")
    except KeyboardInterrupt:
        print("\n\n--- TEST SIMULATION INTERRUPTED ---")
        print("Simulation was stopped by user (Ctrl+C)")


def main():
    # Add command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Run the simulation with UI or in console mode"
    )
    parser.add_argument(
        "--test-mode", action="store_true", help="Run in test mode with sample actions"
    )
    parser.add_argument(
        "--use-notepad",
        action="store_true",
        help="Use notepad instead of knowledge in agent prompts",
    )
    parser.add_argument(
        "--llm-provider",
        type=str,
        default="together",
        choices=["ollama", "together"],
        help="LLM provider to use (ollama or together)",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        help="Model name to use with the LLM provider (e.g., llama3.2 for ollama)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key for providers that require authentication",
    )
    parser.add_argument(
        "--basic-simulation",
        action="store_true",
        help="Use the basic simulation instead of the complex one",
    )
    parser.add_argument(
        "--console-mode", action="store_true", help="Run in console mode without UI"
    )
    parser.add_argument(
        "--turn-strategy",
        type=str,
        default="round_robin",
        choices=["round_robin", "priority", "reactive", "location", "balanced"],
        help="Strategy for determining agent turn order",
    )
    args = parser.parse_args()

    try:
        # Configure the LLM service
        configure_llm(args.llm_provider, args.llm_model, args.api_key)

        if args.console_mode:
            if args.test_mode:
                # Run test mode in console, passing notepad flag
                run_console_test_mode(use_notepad_mode=args.use_notepad)
            else:
                # Run regular simulation in console mode (like in chat.py)
                agents, item_locations = setup_simulation(
                    use_notepad_mode=args.use_notepad,
                    use_complex=not args.basic_simulation,
                )

                # Create and start simulation (no UI)
                simulation = WorldSimulation(
                    agents, item_locations, turn_strategy=args.turn_strategy
                )
                try:
                    simulation.start(threaded=False, delay_between_actions=0.0)
                except KeyboardInterrupt:
                    simulation.stop()  # Try to stop the simulation gracefully
                    print("\n\n--- SIMULATION INTERRUPTED (Ctrl+C) ---")
                    print("Exiting gracefully...")
        else:
            # Create the UI with parsed arguments
            app = WorldUI(
                test_mode=args.test_mode,
                notepad_mode=args.use_notepad,
                basic_simulation=args.basic_simulation,
                turn_strategy=args.turn_strategy,
            )
            app.protocol("WM_DELETE_WINDOW", app.on_closing)
            app.mainloop()
    except KeyboardInterrupt:
        print("\n\n--- PROGRAM INTERRUPTED (Ctrl+C) ---")
        print("Exiting gracefully...")
        sys.exit(0)


if __name__ == "__main__":
    main()
