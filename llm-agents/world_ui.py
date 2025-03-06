from datetime import datetime
import time
import tkinter as tk
from tkinter import ttk
from typing import Dict, Set, List, Optional, Tuple

from agents import Agent
from data import (
    AgentName,
    BeHelpfulMotivation,
    ItemLocation,
    ItemType,
    LocationName,
    SeekMotivation,
    ACTION_ICONS,
    ACTION_SYMBOLS,
)
from simulation import WorldSimulation, setup_simulation


class LocationCell(ttk.Frame):
    def __init__(self, parent, location: str):
        super().__init__(parent, relief="solid", borderwidth=1)
        self.location = location
        self.highlight_task = None

        # Get background color based on location type
        bg_color = self._get_location_color(location)

        # Create a canvas for the background with gradient
        self.bg_canvas = tk.Canvas(self, highlightthickness=0)
        self.bg_canvas.pack(fill="both", expand=True)

        # Create gradient background
        self.bg_canvas.bind("<Configure>", self._draw_background)

        # Create main content frame with padding for highlight border
        self.content = ttk.Frame(self.bg_canvas, style="Transparent.TFrame")
        self.content_window = self.bg_canvas.create_window(
            2, 2, anchor="nw", window=self.content
        )

        # Bind resize event to update content window
        self.bg_canvas.bind("<Configure>", self._on_resize, add="+")

        # Location name at top
        self.name_label = ttk.Label(
            self.content, text=location.upper(), font=("Arial", 12, "bold")
        )
        self.name_label.pack(pady=(5, 0))

        # Frame for agents
        self.agents_frame = ttk.Frame(self.content)
        self.agents_frame.pack(fill="x", pady=5, padx=5)
        ttk.Label(self.agents_frame, text="Agents:", font=("Arial", 10, "italic")).pack(
            anchor="w"
        )
        self.agents_list = ttk.Frame(self.agents_frame)
        self.agents_list.pack(fill="x")

        # Frame for items
        self.items_frame = ttk.Frame(self.content)
        self.items_frame.pack(fill="x", pady=5, padx=5)
        ttk.Label(self.items_frame, text="Items:", font=("Arial", 10, "italic")).pack(
            anchor="w"
        )
        self.items_list = ttk.Frame(self.items_frame)
        self.items_list.pack(fill="x")

        # Track current agents and items
        self.current_agents: Set[str] = set()
        self.current_items: Set[str] = set()

    def _get_location_color(self, location: str) -> str:
        """Get background color based on location type"""
        color_map = {
            "City": "#e0e8ff",  # Light blue for city
            "Field": "#d8f0d8",  # Light green for field
            "Forest": "#c8e8c8",  # Darker green for forest
            "Cave": "#e0e0e0",  # Gray for cave
            "Mountain": "#f0e0c0",  # Tan/brown for mountain
            "Beach": "#fff0c0",  # Light yellow for beach
        }
        return color_map.get(location, "#ffffff")

    def _draw_background(self, event=None):
        """Draw the gradient background for the location"""
        width = self.bg_canvas.winfo_width()
        height = self.bg_canvas.winfo_height()

        if width <= 1 or height <= 1:
            return  # Skip if not fully created yet

        # Clear existing background
        self.bg_canvas.delete("background")

        # Get base color and create a slightly darker variant for gradient
        base_color = self._get_location_color(self.location)

        # Create a gradient from top to bottom
        for i in range(height):
            # Calculate color for this line (blend from base to darker)
            r1, g1, b1 = self.winfo_rgb(base_color)
            r2, g2, b2 = self.winfo_rgb(self._darken_color(base_color))

            # Convert to 8-bit color values
            r1, g1, b1 = r1 // 256, g1 // 256, b1 // 256
            r2, g2, b2 = r2 // 256, g2 // 256, b2 // 256

            # Linear interpolation
            ratio = i / height
            r = int(r1 * (1 - ratio) + r2 * ratio)
            g = int(g1 * (1 - ratio) + g2 * ratio)
            b = int(b1 * (1 - ratio) + b2 * ratio)

            # Create line with this color
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.bg_canvas.create_line(0, i, width, i, fill=color, tags="background")

    def _darken_color(self, color, factor=0.8):
        """Darken a color by the given factor"""
        # Convert from #RRGGBB to integers
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)

        # Darken
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)

        # Ensure values are in range
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"

    def _on_resize(self, event):
        """Update the content window when canvas is resized"""
        width = self.bg_canvas.winfo_width()
        height = self.bg_canvas.winfo_height()

        # Update content window size
        self.bg_canvas.itemconfig(
            self.content_window, width=width - 4, height=height - 4
        )

        # Also redraw the background
        self._draw_background()

    def update_agents(self, agents: Set[str]):
        """Update the agents displayed in this cell"""
        # Clear existing agents
        for widget in self.agents_list.winfo_children():
            widget.destroy()

        # Add new agents
        for agent in sorted(agents):
            agent_frame = ttk.Frame(self.agents_list)
            agent_frame.pack(fill="x", pady=1)

            # Get agent color based on agent name/type
            agent_color = self._get_agent_color(agent)

            # Create agent icon as small colored circle
            icon_canvas = tk.Canvas(
                agent_frame,
                width=16,
                height=16,
                bg="SystemButtonFace",
                highlightthickness=0,
            )
            icon_canvas.pack(side="left", padx=2)
            icon_canvas.create_oval(2, 2, 14, 14, fill=agent_color, outline="black")

            # Agent name
            name_label = ttk.Label(agent_frame, text=agent)
            name_label.pack(side="left", padx=2)

        self.current_agents = agents

    def update_items(self, items: Set[str]):
        """Update the items displayed in this cell"""
        # Clear existing items
        for widget in self.items_list.winfo_children():
            widget.destroy()

        # Add new items
        for item in sorted(items):
            item_frame = ttk.Frame(self.items_list)
            item_frame.pack(fill="x", pady=1)

            # Get item color and icon based on item type
            item_color, item_icon = self._get_item_display(item)

            # Create item icon as a colored shape
            icon_canvas = tk.Canvas(
                item_frame,
                width=16,
                height=16,
                bg="SystemButtonFace",
                highlightthickness=0,
            )
            icon_canvas.pack(side="left", padx=2)

            # Draw based on icon type
            if item_icon == "sword":
                # Draw a simple sword shape
                icon_canvas.create_line(8, 2, 8, 12, width=2, fill=item_color)
                icon_canvas.create_polygon(
                    4, 5, 12, 5, 8, 2, fill=item_color, outline="black"
                )
            elif item_icon == "gem":
                # Draw a diamond shape
                icon_canvas.create_polygon(
                    8, 2, 14, 8, 8, 14, 2, 8, fill=item_color, outline="black"
                )
            else:
                # Default circular icon
                icon_canvas.create_oval(2, 2, 14, 14, fill=item_color, outline="black")

            # Item name
            name_label = ttk.Label(item_frame, text=item)
            name_label.pack(side="left", padx=2)

        self.current_items = items

    def _get_agent_color(self, agent_name: str) -> str:
        """Get color for agent based on name/type"""
        color_map = {
            "Seeker": "#5599ff",  # Blue
            "Knower": "#55aa55",  # Green
            "Helper": "#aa55aa",  # Purple
            # Add more agent types as needed
        }
        # Default color for unknown agents
        return color_map.get(agent_name, "#888888")

    def _get_item_display(self, item_name: str) -> Tuple[str, str]:
        """Get color and icon type for item based on name/type"""
        item_map = {
            "Sword": ("#aa5555", "sword"),  # Red, sword icon
            "Stone": ("#55aaaa", "gem"),  # Teal, gem icon
            # Add more item types as needed
        }
        # Default for unknown items
        return item_map.get(item_name, ("#888888", "default"))

    def highlight_location(self, active: bool = True):
        """Highlight the location cell with a pulsing border"""
        if active:
            self.configure(style="Active.TFrame")
            self._pulse_highlight()
        else:
            self.configure(style="TFrame")
            if self.highlight_task:
                self.after_cancel(self.highlight_task)
                self.highlight_task = None

    def _pulse_highlight(self, step: int = 0):
        """Create a pulsing effect for the active location"""
        colors = ["#ff9999", "#ff8080", "#ff6666", "#ff8080", "#ff9999"]
        if step < len(colors):
            self.configure(style=f"Pulse{step}.TFrame")
            self.highlight_task = self.after(200, self._pulse_highlight, step + 1)
        else:
            self.highlight_task = self.after(1000, self._pulse_highlight, 0)

    def highlight_agent(
        self, agent_name: str, active: bool = True, style: str = "default"
    ):
        """Highlight a specific agent in this cell"""
        for widget in self.agents_list.winfo_children():
            name_label = widget.winfo_children()[-1]  # Last child is the name label
            if name_label["text"] == agent_name:
                if active:
                    if style == "thinking":
                        # Green for thinking state
                        widget.configure(style="Thinking.TFrame")
                        name_label.configure(
                            font=("Arial", 10, "bold"), foreground="green"
                        )
                    else:
                        # Default highlight style
                        widget.configure(style="Active.TFrame")
                        name_label.configure(
                            font=("Arial", 10, "bold"), foreground="black"
                        )
                else:
                    widget.configure(style="TFrame")
                    name_label.configure(font=("Arial", 10), foreground="black")


class WorldGrid(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid_cells: Dict[str, LocationCell] = {}
        self.setup_grid()
        self.setup_styles()

    def setup_styles(self):
        """Setup custom styles for highlighting"""
        style = ttk.Style()

        # Basic active style
        style.configure("Active.TFrame", borderwidth=2, relief="solid")

        # Thinking style (purple border)
        style.configure(
            "Thinking.TFrame", borderwidth=2, relief="solid", background="#e6c4ff"
        )

        # Pulsing highlight styles
        colors = ["#ff9999", "#ff8080", "#ff6666", "#ff8080", "#ff9999"]
        for i, color in enumerate(colors):
            style.configure(
                f"Pulse{i}.TFrame", borderwidth=2, relief="solid", background=color
            )

    def setup_grid(self):
        # Create a frame for the world grid
        self.grid_frame = ttk.Frame(self)
        self.grid_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Configure the grid to have 2 rows and 3 columns
        for i in range(2):
            self.grid_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):
            self.grid_frame.grid_columnconfigure(i, weight=1)

    def create_location_cell(
        self, location: str, row: int, column: int
    ) -> LocationCell:
        """Create a cell representing a location in the grid"""
        cell = LocationCell(self.grid_frame, location)
        cell.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")
        self.grid_cells[location] = cell

        return cell

    def update_location(self, location: str, agents: Set[str], items: Set[str]):
        """Update the contents of a location cell"""
        if location in self.grid_cells:
            cell = self.grid_cells[location]
            cell.update_agents(agents)
            cell.update_items(items)

    def highlight_active_location(self, location: str):
        """Highlight the active location and clear others"""
        for loc, cell in self.grid_cells.items():
            cell.highlight_location(loc == location)

    def highlight_active_agent(
        self, agent: str, location: str = None, style: str = "default"
    ):
        """Highlight an agent in its current location"""
        # If agent is None, clear all highlights
        if agent is None:
            for loc, cell in self.grid_cells.items():
                # Clear highlights for all agents in this cell
                for agent_name in cell.current_agents:
                    cell.highlight_agent(agent_name, False)
            return

        # Otherwise, highlight the specified agent
        for loc, cell in self.grid_cells.items():
            if location is None or loc == location:
                cell.highlight_agent(agent, True, style=style)
            else:
                cell.highlight_agent(agent, False)

    def clear_all_highlights(self):
        """Clear all agent and location highlights"""
        # Clear agent highlights
        self.highlight_active_agent(None)

        # Clear location highlights
        for loc, cell in self.grid_cells.items():
            cell.highlight_location(False)

    def animate_agent_movement(
        self,
        agent_name: str,
        from_location: str,
        to_location: str,
        duration: int = 1000,
        callback=None,
    ):
        """Animate an agent moving between locations"""
        if from_location in self.grid_cells and to_location in self.grid_cells:
            # Create a temporary canvas for the animation
            anim_canvas = tk.Canvas(self, bg="#f0f0f0", highlightthickness=0)
            anim_canvas.place(x=0, y=0, relwidth=1, relheight=1)

            # Get the agent color
            agent_color = self.grid_cells[from_location]._get_agent_color(agent_name)

            # Get start and end positions (center of cells)
            from_cell = self.grid_cells[from_location]
            to_cell = self.grid_cells[to_location]

            # Wait for UI to update before animation
            self.after(
                50,
                lambda: self._run_movement_animation(
                    anim_canvas,
                    agent_name,
                    agent_color,
                    from_cell,
                    to_cell,
                    duration,
                    callback,
                ),
            )

    def _run_movement_animation(
        self, canvas, agent_name, agent_color, from_cell, to_cell, duration, callback
    ):
        """Execute the animation sequence"""
        # Get coordinates
        x1 = from_cell.winfo_x() + from_cell.winfo_width() // 2
        y1 = from_cell.winfo_y() + from_cell.winfo_height() // 2
        x2 = to_cell.winfo_x() + to_cell.winfo_width() // 2
        y2 = to_cell.winfo_y() + to_cell.winfo_height() // 2

        # Create agent representation
        agent_icon = canvas.create_oval(
            x1 - 10, y1 - 10, x1 + 10, y1 + 10, fill=agent_color, outline="black"
        )
        agent_text = canvas.create_text(
            x1, y1, text=agent_name[0], fill="white", font=("Arial", 8, "bold")
        )

        # Animation parameters
        steps = 20
        step_time = duration / steps
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps

        def move_step(step=0):
            if step < steps:
                # Move the agent icon
                canvas.move(agent_icon, dx, dy)
                canvas.move(agent_text, dx, dy)
                # Schedule next step
                self.after(int(step_time), lambda: move_step(step + 1))
            else:
                # Animation complete
                canvas.destroy()
                if callback:
                    callback()

        # Start animation
        move_step()


class ActionLog(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_log()

    def setup_log(self):
        # Title
        self.title = ttk.Label(self, text="Action Log", font=("Arial", 14, "bold"))
        self.title.pack(pady=10)

        # Create scrollable text widget
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True, padx=5)

        # Add scrollbar
        self.scrollbar = ttk.Scrollbar(self.container)
        self.scrollbar.pack(side="right", fill="y")

        # Add text widget
        self.log = tk.Text(
            self.container,
            wrap="word",
            height=8,
            yscrollcommand=self.scrollbar.set,
            font=("Arial", 10),
            state="disabled",
        )
        self.log.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.log.yview)

        # Configure tags for different message types
        self.log.tag_configure("timestamp", foreground="gray")
        self.log.tag_configure("dialogue", foreground="#0066cc")
        self.log.tag_configure("travel", foreground="#006600")
        self.log.tag_configure("search", foreground="#660099")
        self.log.tag_configure("found", foreground="#cc6600")
        self.log.tag_configure("meeting", foreground="#663300")
        self.log.tag_configure("knowledge", foreground="#cc3300")
        self.log.tag_configure("location", foreground="#006633")
        self.log.tag_configure("notepad", foreground="#cc0099")
        self.log.tag_configure("give", foreground="#cc6600")
        self.log.tag_configure("system", foreground="#008080")

        # Use centralized icon definitions
        self.action_icons = ACTION_ICONS
        self.action_symbols = ACTION_SYMBOLS

        # Check if platform supports unicode emoji
        try:
            # Try to display a simple emoji
            test_label = tk.Label(self, text="😀")
            test_label.pack()
            test_label.destroy()

            # Use emoji if no exception
            self.use_emoji = True
        except:
            # Fall back to symbols if there's an issue
            self.use_emoji = False

    def add_action(
        self, agent: str, action_type: str, message: str, target: Optional[str] = None
    ):
        """Add an agent's action to the log with appropriate formatting"""
        self.log.config(state="normal")

        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.insert("end", f"[{timestamp}] ", "timestamp")

        # Get the appropriate icon/symbol
        icon = (
            self.action_icons.get(action_type, "")
            if self.use_emoji
            else self.action_symbols.get(action_type, "")
        )

        # Format based on action type
        if action_type == "dialogue":
            self.log.insert("end", icon, action_type)
            self.log.insert("end", f"{agent} → {target}: ", action_type)
            self.log.insert("end", f"{message}\n")
        elif action_type == "travel":
            self.log.insert("end", icon, action_type)
            self.log.insert("end", f"{agent} moved to {target}", action_type)
            if message:
                self.log.insert("end", f": {message}")
            self.log.insert("end", "\n")
        elif action_type == "search":
            self.log.insert("end", icon, action_type)
            self.log.insert("end", f"{agent} searched for {target}", action_type)
            if message:
                self.log.insert("end", f": {message}")
            self.log.insert("end", "\n")
        elif action_type == "give":
            self.log.insert("end", icon, action_type)
            self.log.insert("end", f"{agent} gave to {target}", action_type)
            if message:
                self.log.insert("end", f": {message}")
            self.log.insert("end", "\n")
        elif action_type == "notepad":
            self.log.insert("end", icon, action_type)
            self.log.insert("end", f"{agent} updated notepad", action_type)
            if message:
                self.log.insert("end", f": {message}")
            self.log.insert("end", "\n")
        else:
            # Generic handling for other action types
            self.log.insert("end", icon, action_type)
            self.log.insert(
                "end", f"{agent} {action_type.replace('_', ' ')}", action_type
            )
            if target:
                self.log.insert("end", f" → {target}", action_type)
            if message:
                self.log.insert("end", f": {message}")
            self.log.insert("end", "\n")

        # Scroll to bottom
        self.log.see("end")
        self.log.config(state="disabled")

    def add_system_message(self, msg_type: str, message: str):
        """Add a system message to the log"""
        self.log.config(state="normal")

        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.insert("end", f"[{timestamp}] ", "timestamp")

        # Check if message already starts with any emoji character
        # Simple heuristic: most emoji and special symbols are outside ASCII range
        has_emoji_prefix = message and ord(message[0]) > 127

        if has_emoji_prefix:
            # Message already has an emoji or special character, don't add another one
            self.log.insert("end", message + "\n", msg_type)
        else:
            # Message doesn't start with an emoji, add one
            icon = (
                self.action_icons.get(msg_type, self.action_icons["system"])
                if self.use_emoji
                else self.action_symbols.get(msg_type, self.action_symbols["system"])
            )
            self.log.insert("end", icon, msg_type)
            self.log.insert("end", message + "\n", msg_type)

        # Scroll to bottom
        self.log.see("end")
        self.log.config(state="disabled")


class StatsPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_panel()

        # Add timing tracking
        self.thinking_times = {}  # {agent_name: total_seconds}
        self.evaluation_times = {}  # {agent_name: total_seconds}
        self.memory_times = {}  # {agent_name: total_seconds} - New for MemoryMinder
        self.thinking_start_times = {}  # {agent_name: start_time}
        self.evaluation_start_times = {}  # {agent_name: start_time}
        self.memory_start_times = {}  # {agent_name: start_time} - New for MemoryMinder

        # Track global stats
        self.total_thinking_time = 0
        self.total_evaluation_time = 0
        self.total_memory_time = 0  # New for MemoryMinder

    def setup_panel(self):
        # Title
        self.title = ttk.Label(self, text="Statistics", font=("Arial", 14, "bold"))
        self.title.pack(pady=(10, 5))

        # Simulation stats section
        self.sim_frame = ttk.LabelFrame(self, text="Simulation Stats", padding=5)
        self.sim_frame.pack(fill="x", padx=5, pady=5)

        # Create two columns for sim stats
        sim_columns_frame = ttk.Frame(self.sim_frame)
        sim_columns_frame.pack(fill="x", expand=True)

        # Left column for time stats
        left_col = ttk.Frame(sim_columns_frame)
        left_col.pack(side="left", fill="y", expand=True, padx=5)

        # Right column for action counts
        right_col = ttk.Frame(sim_columns_frame)
        right_col.pack(side="left", fill="y", expand=True, padx=5)

        # Time stats in left column
        self.time_label = ttk.Label(left_col, text="Time: 00:00")
        self.time_label.pack(anchor="w")

        # Add timing labels to left column
        self.thinking_time_label = ttk.Label(left_col, text="Thinking: 0.0s")
        self.thinking_time_label.pack(anchor="w")

        self.evaluation_time_label = ttk.Label(left_col, text="Evaluating: 0.0s")
        self.evaluation_time_label.pack(anchor="w")

        self.memory_time_label = ttk.Label(left_col, text="Memory: 0.0s")
        self.memory_time_label.pack(anchor="w")

        # Action counts in right column
        self.action_labels = {
            "dialogue_action": ttk.Label(right_col, text="Dialogue: 0"),
            "travel_action": ttk.Label(right_col, text="Travel: 0"),
            "search_action": ttk.Label(right_col, text="Search: 0"),
            "notepad_action": ttk.Label(right_col, text="Notepad: 0"),
            "give_action": ttk.Label(right_col, text="Gifts: 0"),
        }
        for label in self.action_labels.values():
            label.pack(anchor="w")

        # Create a LabelFrame for agent information with a clear title
        self.agents_label_frame = ttk.LabelFrame(self, text="Agent Status", padding=5)
        self.agents_label_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create a frame to hold both scrollbars and canvas
        scroll_container = ttk.Frame(self.agents_label_frame)
        scroll_container.pack(fill="both", expand=True)

        # Create a canvas for scrolling with fixed height to ensure scroll works properly
        self.agents_canvas = tk.Canvas(scroll_container, height=300)
        self.agents_canvas.pack(side="left", fill="both", expand=True)

        # Add vertical scrollbar
        self.v_scrollbar = ttk.Scrollbar(
            scroll_container, orient="vertical", command=self.agents_canvas.yview
        )
        self.v_scrollbar.pack(side="right", fill="y")

        # Add horizontal scrollbar
        self.h_scrollbar = ttk.Scrollbar(
            self.agents_label_frame,
            orient="horizontal",
            command=self.agents_canvas.xview,
        )
        self.h_scrollbar.pack(side="bottom", fill="x")

        # Configure canvas to use both scrollbars
        self.agents_canvas.configure(
            yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set
        )

        # Create a frame inside the canvas for agent frames
        self.agents_frame = ttk.Frame(self.agents_canvas)

        # Add the agent frame to the canvas - don't constrain width
        self.agents_canvas_window = self.agents_canvas.create_window(
            (0, 0), window=self.agents_frame, anchor="nw"
        )

        # Configure canvas scrolling by binding to frame size changes
        self.agents_frame.bind("<Configure>", self._on_frame_configure)
        self.agents_canvas.bind("<Configure>", self._on_canvas_configure)

        # Make mouse wheel scroll the canvas
        self.agents_canvas.bind_all("<MouseWheel>", self._on_mousewheel_vertical)
        # Add shift+mousewheel for horizontal scrolling
        self.agents_canvas.bind_all(
            "<Shift-MouseWheel>", self._on_mousewheel_horizontal
        )

        # Dictionary to store agent info frames
        self.agent_frames = {}

    def _on_frame_configure(self, event=None):
        """Update the scrollregion when the inner frame changes size"""
        # Update the scrollregion to encompass the inner frame
        self.agents_canvas.configure(scrollregion=self.agents_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Update the inner frame when the canvas changes size"""
        # Set minimum width to the canvas width, but allow it to be larger
        min_width = event.width
        if self.agents_frame.winfo_reqwidth() < min_width:
            self.agents_canvas.itemconfig(self.agents_canvas_window, width=min_width)

    def _on_mousewheel_vertical(self, event):
        """Handle vertical mouse wheel scrolling"""
        self.agents_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_horizontal(self, event):
        """Handle horizontal mouse wheel scrolling (with Shift key)"""
        self.agents_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def update_time(self, seconds: int):
        """Update the elapsed time display"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        self.time_label.config(text=f"Time: {hours:02d}:{minutes:02d}:{seconds:02d}")

        # Update timing stats (base values without in-progress times)
        self.thinking_time_label.config(
            text=f"Thinking: {self.total_thinking_time:.1f}s"
        )
        self.evaluation_time_label.config(
            text=f"Evaluating: {self.total_evaluation_time:.1f}s"
        )
        self.memory_time_label.config(text=f"Memory: {self.total_memory_time:.1f}s")

    def update_action_counts(self, counts: dict):
        """Update all action counts from WorldState stats"""
        for action_type, count in counts.items():
            action_name = action_type.replace("_action", "").title()
            self.action_labels[action_type].config(text=f"{action_name}: {count}")

    def update_agent(
        self,
        name: str,
        location: str,
        inventory: set,
        motivation: str,
        knowledge: str,
        notes: List[str] = None,
        show_knowledge: bool = True,
    ):
        """Update or create an agent's status display"""
        if name not in self.agent_frames:
            # Create new agent frame with distinct visual separation
            frame = ttk.Frame(self.agents_frame)
            frame.pack(fill="x", padx=2, pady=5)

            # Add a separator above each agent (except the first one)
            if len(self.agent_frames) > 0:
                separator = ttk.Separator(frame, orient="horizontal")
                separator.pack(fill="x", pady=(0, 5))

            # Use a more distinct header for each agent
            header_frame = ttk.Frame(frame)
            header_frame.pack(fill="x", pady=2)

            # Agent name with background color based on agent type
            name_color = self._get_agent_color(name)
            name_label = tk.Label(
                header_frame,
                text=name,
                font=("Arial", 11, "bold"),
                bg=name_color,
                fg="white",
                padx=5,
            )
            name_label.pack(side="left")

            # Status indicator (with enough space for status text)
            status_frame = ttk.Frame(header_frame)
            status_frame.pack(side="right")

            status_prefix = ttk.Label(status_frame, text="Status:")
            status_prefix.pack(side="left", padx=(0, 5))

            status_value = ttk.Label(
                status_frame, text="Ready", foreground="blue", width=25
            )
            status_value.pack(side="left")

            # Create a more compact layout for agent info
            info_frame = ttk.Frame(frame)
            info_frame.pack(fill="x", expand=True, pady=2)

            # Split into left and right columns for more efficient space usage
            left_col = ttk.Frame(info_frame)
            left_col.pack(side="left", fill="y", padx=2)

            right_col = ttk.Frame(info_frame)
            right_col.pack(side="right", fill="y", padx=2)

            # Place basic info in left column
            loc_label = ttk.Label(left_col, text="Location: ")
            loc_label.pack(anchor="w")

            inv_label = ttk.Label(left_col, text="Inventory: ")
            inv_label.pack(anchor="w")

            # Place motivation and timing in right column
            motivation_label = ttk.Label(right_col, text="Motivation: ")
            motivation_label.pack(anchor="w")

            timing_label = ttk.Label(right_col, text="Time: 0.0s / 0.0s / 0.0s")
            timing_label.pack(anchor="w")

            # Knowledge label below the columns (collapsible)
            knowledge_frame = ttk.Frame(frame)
            knowledge_frame.pack(fill="x", pady=2)

            knowledge_header = ttk.Label(
                knowledge_frame, text="Knowledge:", font=("Arial", 9, "bold")
            )
            knowledge_header.pack(anchor="w")

            knowledge_label = ttk.Label(knowledge_frame, text="", wraplength=350)
            knowledge_label.pack(anchor="w", padx=10, fill="x", expand=True)

            # Create a frame for notes with better visibility
            notes_frame = ttk.Frame(frame)
            notes_frame.pack(fill="x", expand=True, pady=2)

            # Header row with title and expand button
            notes_header = ttk.Frame(notes_frame)
            notes_header.pack(fill="x", expand=True)

            notes_title = ttk.Label(
                notes_header, text="Notes:", font=("Arial", 9, "bold")
            )
            notes_title.pack(side="left", anchor="w")

            # Add view all button
            view_all_btn = ttk.Button(
                notes_header,
                text="View All",
                width=8,
                command=lambda n=name: self._show_all_notes(n),
            )
            view_all_btn.pack(side="right", padx=5)

            # Notes container (existing code continues)
            notes_container = ttk.Frame(notes_frame)
            notes_container.pack(fill="x", expand=True)

            # Make notes area taller (5 lines instead of 2)
            notes_text = tk.Text(
                notes_container, height=5, width=45, wrap="word", font=("Arial", 9)
            )
            scrollbar = ttk.Scrollbar(
                notes_container, orient="vertical", command=notes_text.yview
            )
            notes_text.configure(yscrollcommand=scrollbar.set)

            notes_text.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Store all widgets in the agent_frames dictionary
            self.agent_frames[name] = {
                "frame": frame,
                "name_label": name_label,
                "location": loc_label,
                "inventory": inv_label,
                "motivation": motivation_label,
                "knowledge_frame": knowledge_frame,
                "knowledge_header": knowledge_header,
                "knowledge": knowledge_label,
                "notes_text": notes_text,
                "notes_scrollbar": scrollbar,
                "view_all_btn": view_all_btn,
                "status_prefix": status_prefix,
                "status": status_value,
                "timing": timing_label,
            }

            # Initialize timing tracking for this agent
            self.thinking_times[name] = 0.0
            self.evaluation_times[name] = 0.0
            self.memory_times[name] = 0.0  # Initialize memory time

        # Update all agent information
        self.agent_frames[name]["location"].config(text=f"Location: {location}")

        inventory_str = (
            ", ".join(item for item in inventory) if inventory else "<Empty>"
        )
        self.agent_frames[name]["inventory"].config(text=f"Inventory: {inventory_str}")

        self.agent_frames[name]["motivation"].config(text=f"Motivation: {motivation}")

        # Show or hide knowledge based on the show_knowledge flag
        if show_knowledge:
            # Only show first few chars of knowledge to save space
            knowledge_summary = (
                knowledge[:100] + "..." if len(knowledge) > 100 else knowledge
            )
            self.agent_frames[name]["knowledge"].config(text=knowledge_summary)
            self.agent_frames[name]["knowledge_frame"].pack(
                fill="x", pady=2
            )  # Ensure it's visible
        else:
            self.agent_frames[name][
                "knowledge_frame"
            ].pack_forget()  # Hide the knowledge section

        # Update notes using the text widget for better display
        notes_text = self.agent_frames[name]["notes_text"]
        notes_text.config(state="normal")
        notes_text.delete("1.0", "end")

        if notes and len(notes) > 0:
            for i, note in enumerate(notes):
                notes_text.insert("end", f"• {note}\n")

            # Enable the view all button if there are notes
            if "view_all_btn" in self.agent_frames[name]:
                self.agent_frames[name]["view_all_btn"].state(["!disabled"])
        else:
            notes_text.insert("end", "No notes yet")
            # Disable the view all button if there are no notes
            if "view_all_btn" in self.agent_frames[name]:
                self.agent_frames[name]["view_all_btn"].state(["disabled"])

        notes_text.config(state="disabled")

        # Update timing information
        self._update_agent_timing_display(name)

        # After updating, ensure scrollregion is updated for both dimensions
        self._on_frame_configure()

    def _get_agent_color(self, agent_name: str) -> str:
        """Get color for agent based on name/type"""
        color_map = {
            "Seeker": "#5599ff",  # Blue
            "Knower": "#55aa55",  # Green
            "Helper": "#aa55aa",  # Purple
            # Add more agent types as needed
        }
        # Default color for unknown agents
        return color_map.get(agent_name, "#888888")

    def set_agent_thinking(self, name: str, is_thinking: bool = True):
        """Update agent's thinking status and start/stop timer"""
        if name in self.agent_frames:
            if is_thinking:
                self.agent_frames[name]["status"].config(
                    text="Thinking...", foreground="purple"
                )
                # Start thinking timer
                self.thinking_start_times[name] = time.time()

                # Request the main UI to highlight this agent
                if hasattr(self, "parent_ui") and self.parent_ui:
                    self.parent_ui.highlight_thinking_agent(name)
            else:
                self.agent_frames[name]["status"].config(
                    text="Ready", foreground="blue"
                )
                # Stop thinking timer and add to total
                if name in self.thinking_start_times:
                    elapsed = time.time() - self.thinking_start_times[name]
                    self.thinking_times[name] += elapsed
                    self.total_thinking_time += elapsed
                    del self.thinking_start_times[name]
                    self._update_agent_timing_display(name)

                    # Request the main UI to stop highlighting this agent
                    if hasattr(self, "parent_ui") and self.parent_ui:
                        self.parent_ui.stop_highlighting_thinking_agent(name)

    def set_supervisor_status(self, name: str, status: str, is_approved: bool = None):
        """Update the agent status for supervisor evaluation and handle evaluation timing"""
        if name in self.agent_frames:
            # Set color and status text based on approval status
            if is_approved is None:
                # Evaluating
                self.agent_frames[name]["status"].config(
                    text="Evaluating Next Action...", foreground="orange"
                )
                # Start evaluation timer
                self.evaluation_start_times[name] = time.time()
            elif is_approved:
                # Approved
                self.agent_frames[name]["status"].config(
                    text="Ready", foreground="blue"
                )
                # Stop evaluation timer
                self._stop_evaluation_timer(name)
            else:
                # Rejected with reason
                reason = status.replace("Rejected: ", "")
                truncated_reason = (reason[:30] + "...") if len(reason) > 30 else reason
                self.agent_frames[name]["status"].config(
                    text=f"Action Rejected - {truncated_reason}", foreground="red"
                )
                # Stop evaluation timer
                self._stop_evaluation_timer(name)

    def _stop_evaluation_timer(self, name: str):
        """Helper method to stop the evaluation timer"""
        if name in self.evaluation_start_times:
            elapsed = time.time() - self.evaluation_start_times[name]
            self.evaluation_times[name] += elapsed
            self.total_evaluation_time += elapsed
            del self.evaluation_start_times[name]
            self._update_agent_timing_display(name)

    def set_memory_minder_status(self, name: str, is_recording: bool = True):
        """Update agent status for managing memory and track time"""
        if name in self.agent_frames:
            if is_recording:
                self.agent_frames[name]["status"].config(
                    text="Managing Memory...", foreground="hotpink"
                )
                # Start memory timer
                self.memory_start_times[name] = time.time()
            else:
                self.agent_frames[name]["status"].config(
                    text="Ready", foreground="blue"
                )
                # Stop memory timer and add to total
                if name in self.memory_start_times:
                    elapsed = time.time() - self.memory_start_times[name]
                    self.memory_times[name] += elapsed
                    self.total_memory_time += elapsed
                    del self.memory_start_times[name]
                    self._update_agent_timing_display(name)

    def _update_agent_timing_display(self, name: str):
        """Update the timing display for an agent"""
        if (
            name in self.agent_frames
            and name in self.thinking_times
            and name in self.evaluation_times
            and name in self.memory_times
        ):
            think_time = self.thinking_times[name]
            eval_time = self.evaluation_times[name]
            mem_time = self.memory_times[name]
            self.agent_frames[name]["timing"].config(
                text=f"Time (think/eval/mem): {think_time:.1f}s / {eval_time:.1f}s / {mem_time:.1f}s"
            )

    def update_in_progress_timings(self):
        """Update timings for in-progress operations in real time"""
        current_time = time.time()

        # Calculate temporary totals including active timers
        temp_thinking_time = self.total_thinking_time
        temp_evaluation_time = self.total_evaluation_time
        temp_memory_time = self.total_memory_time

        # Add in-progress thinking times
        for agent, start_time in self.thinking_start_times.items():
            temp_thinking_time += current_time - start_time

        # Add in-progress evaluation times
        for agent, start_time in self.evaluation_start_times.items():
            temp_evaluation_time += current_time - start_time

        # Add in-progress memory times
        for agent, start_time in self.memory_start_times.items():
            temp_memory_time += current_time - start_time

        # Update the labels with the temporary totals
        self.thinking_time_label.config(text=f"Thinking: {temp_thinking_time:.1f}s")
        self.evaluation_time_label.config(
            text=f"Evaluating: {temp_evaluation_time:.1f}s"
        )
        self.memory_time_label.config(text=f"Memory: {temp_memory_time:.1f}s")

        # Also update individual agent timing displays
        for agent in self.agent_frames:
            self._update_agent_in_progress_timing(agent, current_time)

    def _update_agent_in_progress_timing(self, name: str, current_time: float):
        """Update in-progress timing display for an individual agent"""
        if (
            name in self.agent_frames
            and name in self.thinking_times
            and name in self.evaluation_times
            and name in self.memory_times
        ):
            # Start with the accumulated times
            think_time = self.thinking_times[name]
            eval_time = self.evaluation_times[name]
            mem_time = self.memory_times[name]

            # Add any active timing
            if name in self.thinking_start_times:
                think_time += current_time - self.thinking_start_times[name]
            if name in self.evaluation_start_times:
                eval_time += current_time - self.evaluation_start_times[name]
            if name in self.memory_start_times:
                mem_time += current_time - self.memory_start_times[name]

            # Update the display
            self.agent_frames[name]["timing"].config(
                text=f"Time (think/eval/mem): {think_time:.1f}s / {eval_time:.1f}s / {mem_time:.1f}s"
            )

    def _show_all_notes(self, agent_name):
        """Show all notes for an agent in a popup window"""
        if agent_name not in self.agent_frames:
            return

        # Get the notes from the text widget
        notes_text = self.agent_frames[agent_name]["notes_text"]
        notes_content = notes_text.get(
            "1.0", "end-1c"
        )  # Get all text except trailing newline

        # Create popup window
        popup = tk.Toplevel(self)
        popup.title(f"{agent_name}'s Notes")
        popup.geometry("500x400")
        popup.minsize(400, 300)

        # Add a frame with padding
        main_frame = ttk.Frame(popup, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Title with agent name
        title_label = ttk.Label(
            main_frame, text=f"{agent_name}'s Notes", font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Text widget for notes with scrollbar
        notes_frame = ttk.Frame(main_frame)
        notes_frame.pack(fill="both", expand=True)

        popup_text = tk.Text(
            notes_frame, wrap="word", font=("Arial", 11), padx=5, pady=5
        )

        scrollbar = ttk.Scrollbar(
            notes_frame, orient="vertical", command=popup_text.yview
        )
        popup_text.configure(yscrollcommand=scrollbar.set)

        # Pack text and scrollbar
        popup_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Insert notes content
        popup_text.insert("1.0", notes_content)

        # Make the text widget read-only
        popup_text.config(state="disabled")

        # Add a close button
        close_btn = ttk.Button(main_frame, text="Close", command=popup.destroy)
        close_btn.pack(pady=10)

        # Focus the popup window
        popup.focus_set()

        # Make popup window modal
        popup.transient(self)
        popup.grab_set()


class WorldUI(tk.Tk):
    def __init__(
        self,
        test_mode: bool = False,
        notepad_mode: bool = False,
        basic_simulation: bool = False,
        turn_strategy: str = "balanced",
    ):
        super().__init__()
        self.test_mode = test_mode
        self.notepad_mode = notepad_mode
        self.basic_simulation = basic_simulation
        self.turn_strategy = turn_strategy

        # Initialize simulation variable
        self.simulation = None

        self.title("World Simulation UI" + (" (Notepad Mode)" if notepad_mode else ""))

        self.geometry("1200x800")

        # Create main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure grid weights
        self.main_container.grid_columnconfigure(
            0, weight=2
        )  # World grid gets more space
        self.main_container.grid_columnconfigure(1, weight=1)  # Info panels
        self.main_container.grid_rowconfigure(0, weight=2)  # Upper section
        self.main_container.grid_rowconfigure(1, weight=1)  # Action log

        # Create the world grid
        self.world_grid = WorldGrid(self.main_container)
        self.world_grid.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Create stats panel
        self.stats_panel = StatsPanel(self.main_container)
        self.stats_panel.parent_ui = self
        self.stats_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Create action log
        self.action_log = ActionLog(self.main_container)
        self.action_log.grid(
            row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5
        )

        # Add initial locations
        self.world_grid.create_location_cell(LocationName.CITY.value, 0, 0)
        self.world_grid.create_location_cell(LocationName.FIELD.value, 0, 1)
        if not self.basic_simulation:
            self.world_grid.create_location_cell(LocationName.FOREST.value, 0, 2)
            self.world_grid.create_location_cell(LocationName.CAVE.value, 1, 0)
            self.world_grid.create_location_cell(LocationName.MOUNTAIN.value, 1, 1)
            self.world_grid.create_location_cell(LocationName.BEACH.value, 1, 2)

        # Initialize simulation start time
        self.start_time = datetime.now()

        # Initialize simulation or test mode
        if self.test_mode:
            self.setup_test_mode()
        else:
            self.setup_simulation()

        # Start the update timer AFTER the simulation is created
        self.update_stats()

    def update_stats(self):
        """Update statistics periodically"""
        # Only update if the simulation exists and is still running
        if self.simulation and self.simulation.running:
            elapsed = (datetime.now() - self.start_time).seconds
            self.stats_panel.update_time(elapsed)

            # Update any in-progress timings
            self.stats_panel.update_in_progress_timings()

            # Schedule the next update
            self.after(1000, self.update_stats)

    def setup_simulation(self):
        """Setup and start the simulation"""
        # Get simulation setup from shared module
        agents, item_locations = setup_simulation(
            use_notepad_mode=self.notepad_mode, use_complex=not self.basic_simulation
        )

        # Create and start simulation with UI
        self.simulation = WorldSimulation(
            agents, item_locations, ui=self, turn_strategy=self.turn_strategy
        )
        self.simulation.start(threaded=True, delay_between_actions=2.0)

    def setup_test_mode(self):
        """Setup test mode with sample actions"""
        # Add some sample data
        self.world_grid.update_location(
            LocationName.CITY.value,
            [AgentName.SEEKER.value, AgentName.KNOWER.value],
            {ItemType.STONE.value},
        )
        self.world_grid.update_location(
            LocationName.FIELD.value, list(), {ItemType.SWORD.value}
        )

        # Create minimal agents for test mode

        # Create a seeker and knower agent
        seeker_agent = Agent(
            name="Seeker",
            current_location="City",
            known_items=[ItemType.SWORD],
            known_locations={"City", "Field"},
            known_agents=["Knower"],
            motivation=SeekMotivation(item_type=ItemType.SWORD),
        )

        knower_agent = Agent(
            name="Knower",
            current_location="City",
            known_items=[ItemType.SWORD],
            known_locations={"City", "Field"},
            known_agents=["Seeker"],
            motivation=BeHelpfulMotivation(),
        )

        # Add knowledge to Knower
        knower_agent.knowledge.item_locations.append(
            ItemLocation(item_type=ItemType.SWORD, location=LocationName.FIELD)
        )

        # Create item locations
        item_locations = [
            ItemLocation(item_type=ItemType.STONE, location=LocationName.CITY),
            ItemLocation(item_type=ItemType.SWORD, location=LocationName.FIELD),
        ]

        # Initialize a minimal simulation for test mode
        self.simulation = WorldSimulation(
            [seeker_agent, knower_agent], item_locations, ui=self
        )

        # Set running to true but don't actually start the simulation thread
        self.simulation.running = True

        # Initialize agent status panels in the stats display
        self.stats_panel.update_agent(
            name="Seeker",
            location="City",
            inventory=[],
            motivation="Seek → Sword",
            knowledge="  Places: City, Field\n  Agents: Knower",
            notes=["Look for the sword", "Ask Knower for help"]
            if self.notepad_mode
            else [],
            show_knowledge=not self.notepad_mode,
        )

        self.stats_panel.update_agent(
            name="Knower",
            location="City",
            inventory=[],
            motivation="Be Helpful",
            knowledge="  Items: Sword → Field\n  Places: City, Field\n  Agents: Seeker",
            notes=["The Sword is in the Field", "Help Seeker find it"]
            if self.notepad_mode
            else [],
            show_knowledge=not self.notepad_mode,
        )

        # Add sample actions with delays, including thinking time simulation
        def add_action_with_highlight(agent, action_type, message, target, delay):
            # Simulate "thinking" time before each action for 1 second
            self.after(
                delay - 1000, lambda: self.stats_panel.set_agent_thinking(agent, True)
            )

            # Use lambdas with agent name for supervisor status
            self.after(
                delay - 800,
                lambda: self.stats_panel.set_supervisor_status(agent, "Evaluating"),
            )
            self.after(
                delay - 300,
                lambda: self.stats_panel.set_supervisor_status(agent, "Idle"),
            )

            # Use lambdas with agent name for memory minder
            self.after(
                delay - 600,
                lambda: self.stats_panel.set_memory_minder_status(agent, True),
            )
            self.after(
                delay - 300,
                lambda: self.stats_panel.set_memory_minder_status(agent, False),
            )

            # Stop thinking when performing action
            self.after(
                delay - 100, lambda: self.stats_panel.set_agent_thinking(agent, False)
            )

            # Perform the actual action
            self.after(
                delay,
                lambda: self._perform_action_with_highlight(
                    agent, action_type, message, target
                ),
            )

        # Schedule sample actions
        add_action_with_highlight(
            "Seeker",
            "dialogue_action",
            "Do you know where the Sword is?",
            "Knower",
            1000,
        )
        add_action_with_highlight(
            "Knower", "dialogue_action", "Yes, it's in the field!", "Seeker", 3000
        )
        add_action_with_highlight(
            "Seeker", "travel_action", "I must find the sword!", "Field", 5000
        )
        add_action_with_highlight(
            "Seeker", "search_action", "Looking carefully...", "Sword", 7000
        )
        add_action_with_highlight("Seeker", "found_item", None, "Sword", 9000)

    def _perform_action_with_highlight(self, agent, action_type, message, target):
        """Perform a sample action with appropriate UI highlights for test mode"""
        # Get current stats from world state
        stats = self.simulation.world_state.get_stats()

        # Update action counts
        if action_type in stats["action_counts"]:
            # Increment the count for this action type
            stats["action_counts"][action_type] += 1

        # Update the stats panel
        self.stats_panel.update_action_counts(stats["action_counts"])

        # Update action log based on action type
        if action_type == "dialogue_action":
            self.action_log.add_action(agent, "dialogue", message, target)
            # Highlight both agents
            self.highlight_agent_temporarily(agent)
            # self.highlight_agent_temporarily(target)

        elif action_type == "travel_action":
            self.action_log.add_action(agent, "travel", message, target)
            # Find correct location name (case-insensitive)
            target_location = None
            for location in self.world_grid.grid_cells:
                if location.lower() == target.lower():
                    target_location = location
                    break

            if not target_location:
                print(f"Warning: Location '{target}' not found in grid cells")
                return

            # Find agent's current location
            current_location = None
            for location, cell in self.world_grid.grid_cells.items():
                if agent in cell.current_agents:
                    current_location = location
                    break

            if not current_location:
                print(f"Warning: Agent '{agent}' not found in any location")
                return

            # Move the agent from current location to target location
            self.world_grid.update_location(
                current_location,
                [
                    a
                    for a in self.world_grid.grid_cells[current_location].current_agents
                    if a != agent
                ],
                self.world_grid.grid_cells[current_location].current_items,
            )
            self.world_grid.update_location(
                target_location,
                list(self.world_grid.grid_cells[target_location].current_agents)
                + [agent],
                self.world_grid.grid_cells[target_location].current_items,
            )

            # Highlight location and agent
            self.highlight_location_temporarily(target_location)
            self.highlight_agent_temporarily(agent)

        elif action_type == "search_action":
            self.action_log.add_action(agent, "search", message, target)
            # Highlight agent and field location
            self.highlight_agent_temporarily(agent)
            self.highlight_location_temporarily(LocationName.FIELD.value)

        elif action_type == "found_item":
            self.action_log.add_system_message("found", f"{agent} found the {target}!")

            # Remove the found item from the location
            current_location = "Field"  # Seeker is in Field when finding the sword
            current_items = self.world_grid.grid_cells[current_location].current_items

            # Create a new set without the found item
            updated_items = {item for item in current_items if item != target}

            # Update the location without the found item
            self.world_grid.update_location(
                current_location,
                self.world_grid.grid_cells[current_location].current_agents,
                updated_items,
            )

            # Update agent's inventory in stats panel
            self.stats_panel.update_agent(
                name=agent,
                inventory=[target],
                location=current_location,
                motivation="Seek → Sword",
                knowledge="none",
                notes=[],
                show_knowledge=not self.notepad_mode,
            )

            # If this is the final action, stop the simulation
            if target == "Sword":  # or whatever your victory condition is
                self.on_victory()
                self.simulation.logger.log_system_message(
                    "system",
                    "--- TEST SIMULATION COMPLETE ---\nIn a real simulation, agents would make decisions using LLMs",
                )

    def stop_simulation(self):
        """Stop the simulation and timer updates"""
        self.simulation.running = False

    def on_victory(self):
        """Handle victory event"""
        # Stop the simulation
        self.stop_simulation()

        # Calculate duration for consistency with simulation's calculation
        duration = (datetime.now() - self.start_time).total_seconds()

        # Always use the simulation's stats
        stats = self.simulation.world_state.get_stats()

        # Log the victory with the stats
        self.simulation.logger.log_victory(duration, stats)

    def on_closing(self):
        """Handle window closing"""
        try:
            # Only try to stop simulation if it exists
            if hasattr(self, "simulation"):
                self.simulation.stop()
            self.quit()
        except Exception as e:
            print(f"Error stopping simulation: {e}")
            self.quit()

    def highlight_agent_temporarily(self, agent_name, duration=1500):
        """Highlight an agent temporarily and clear after duration."""
        # First clear any existing highlights to avoid multiple highlights
        self.world_grid.highlight_active_agent(None)

        # Then highlight the requested agent
        self.world_grid.highlight_active_agent(agent_name)

        # Schedule clearing this highlight after the duration
        self.after(duration, lambda: self.world_grid.highlight_active_agent(None))

    def highlight_location_temporarily(self, location_name, duration=1500):
        """Highlight a location temporarily and clear after duration."""
        # Clear existing location highlights first
        for loc in self.world_grid.grid_cells:
            self.world_grid.grid_cells[loc].highlight_location(False)

        # Highlight the requested location
        self.world_grid.highlight_active_location(location_name)

        # Schedule clearing
        self.after(duration, lambda: self.world_grid.highlight_active_location(None))

    def highlight_thinking_agent(self, agent_name):
        """Highlight an agent who is currently thinking"""
        # Use a different style for thinking agents (maybe a pulsing glow)
        self.world_grid.highlight_active_agent(agent_name, style="thinking")

        # Store the agent name so we know who's thinking
        if not hasattr(self, "thinking_agents"):
            self.thinking_agents = set()
        self.thinking_agents.add(agent_name)

    def stop_highlighting_thinking_agent(self, agent_name):
        """Stop highlighting a thinking agent"""
        # Clear the agent from thinking state
        if hasattr(self, "thinking_agents"):
            self.thinking_agents.discard(agent_name)

        # Only clear the highlight if we're not about to perform an action with this agent
        # This avoids flickering between thinking highlight and action highlight
        # The action highlight will be cleared by its own timer
