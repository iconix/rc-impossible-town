class SimpleTownMap {
  constructor() {
    this.CELL_TYPES = {
      GRASS: 0,
      PATH: 1,
      BUILDING: 2,
      STREAM: 3,
      KNOWLEDGE_GARDEN: 4,
      PROJECT_GARDEN: 5,
      SNORLAX: 6,
      FOREST: 7,
      FOREST_ENTRANCE: 8
    };

    // map layout (20x20 grid)
    this.map = this.createMap();

    // player spawn position
    this.player = { x: 8, y: 10 };

    // building descriptions
    this.descriptions = {
      'H': 'The Archive: Where I\'ve been',
      'C': 'Hack Space: What I am working on',
      'R': 'Reading Room: Curl up with a good book',
      'A': 'Art Gallery: Pretty things',
      'M': 'Memory Circle: Leave something behind',
      'B': 'Bandstand: An audio journey',
      'S': 'Steam Corner: An industrial landmark',
      'P': 'Play Court: Who\'s got next?',
      'T': 'Town Square: Hear ye! Hear ye!',
      'D': 'Seaplane Dock: Watch the comings and goings'
    };

    this.init();
  }

  createMap() {
    // create empty map
    const map = Array(20).fill().map(() => Array(20).fill(this.CELL_TYPES.GRASS));

    // add all paths
    const paths = [
      // main horizontal and vertical paths
      ...Array(20).fill().map((_, i) => [i, 10]),     // horizontal
      ...Array(17).fill().map((_, i) => [10, i + 3]), // vertical

      // building connection paths
      ...[6,7,8,9].map(y => [2, y]),  // Museum of History vertical
      ...[6,7,8,9].map(y => [6, y]),  // Computer Lab vertical
      ...[6,7,8,9].map(y => [15, y]), // Library vertical

      // Town Square surroundings
      [9, 9], [10, 9], [11, 9],    // top
      [9, 11], [10, 11], [11, 11], // bottom

      // diagonal paths
      [8, 12], [7, 13], [6, 14],   // left diagonal
      [12, 12], [13, 13], [14, 14], // right diagonal

      // path to forest
      [18, 10], [18, 11], [18, 12], [18, 13]
    ];

    paths.forEach(([x, y]) => {
      map[y][x] = this.CELL_TYPES.PATH;
    });

    // add stream
    for (let i = 0; i < 20; i++) {
      map[2][i] = this.CELL_TYPES.STREAM;
    }

    // add buildings with symbols
    const buildings = [
      { x: 2, y: 1, symbol: 'S' },   // Steam Corner
      { x: 2, y: 5, symbol: 'H' },   // History Museum
      { x: 6, y: 5, symbol: 'C' },   // Computer Lab
      { x: 15, y: 5, symbol: 'R' },  // Reading Room
      { x: 2, y: 15, symbol: 'A' },  // Art Museum
      { x: 13, y: 16, symbol: 'P' }, // Play Court
      { x: 16, y: 14, symbol: 'M' }, // Memory Circle
      { x: 15, y: 15, symbol: 'B' }, // Bandstand
      { x: 10, y: 10, symbol: 'T' }, // Town Square
      { x: 18, y: 2, symbol: 'D' }   // Seaplane Dock
    ];

    buildings.forEach(b => {
      map[b.y][b.x] = { type: this.CELL_TYPES.BUILDING, symbol: b.symbol };
    });

    // add gardens
    const knowledgeGarden = [
      [16, 5], [17, 5], [18, 5],
      [16, 6], [17, 6], [18, 6],
      [16, 7], [17, 7], [18, 7]
    ];

    const projectGarden = [
      [3, 14], [4, 14], [5, 14],
      [3, 15], [4, 15], [5, 15],
      [3, 16], [4, 16], [5, 16]
    ];

    knowledgeGarden.forEach(([x, y], i) => {
      map[y][x] = {
        type: this.CELL_TYPES.KNOWLEDGE_GARDEN,
        isCenter: i === 4  // center tile (middle of 3x3 grid)
      };
    });

    projectGarden.forEach(([x, y], i) => {
      map[y][x] = {
        type: this.CELL_TYPES.PROJECT_GARDEN,
        isCenter: i === 4  // center tile (middle of 3x3 grid)
      };
    });

    // add forest entrance
    map[14][18] = {
      type: this.CELL_TYPES.FOREST_ENTRANCE,
      isCenter: true
    };

    const forestTiles = [
      [19, 11], [19, 12], [19, 13], [19, 14],
      [18, 15], [19, 15], [18, 16], [19, 16],
      [18, 17], [19, 17], [18, 18], [19, 18],
      [18, 19], [19, 19]
    ];

    forestTiles.forEach(([x, y]) => {
      map[y][x] = this.CELL_TYPES.FOREST;
    });

    // Add Snorlax
    map[17][17] = this.CELL_TYPES.SNORLAX;

    return map;
  }

  init() {
    // Create container
    const container = document.createElement('div');
    container.className = 'w-full max-w-5xl mx-auto p-4 bg-yellow-50 min-h-screen';

    // Add title
    const title = document.createElement('div');
    title.className = 'text-xl mb-2 text-center font-bold';
    title.textContent = 'nadj.land';
    container.appendChild(title);

    // Add location display
    const location = document.createElement('div');
    location.id = 'location';
    location.className = 'h-6 mb-2 text-center';
    location.textContent = 'walking around town...';
    container.appendChild(location);

    // Create map grid
    const grid = document.createElement('div');
    grid.className = 'grid gap-0 mx-auto';
    grid.style.gridTemplateColumns = 'repeat(20, minmax(0, 1fr))';
    grid.style.width = 'min(100%, 640px)';

    // Create cells
    for (let y = 0; y < 20; y++) {
      for (let x = 0; x < 20; x++) {
        const cell = document.createElement('div');
        cell.className = 'w-8 h-8 border border-gray-700 flex items-center justify-center';
        cell.id = `cell-${x}-${y}`;
        grid.appendChild(cell);
      }
    }
    container.appendChild(grid);

    // Add D-pad controls
    const controls = document.createElement('div');
    controls.className = 'grid grid-cols-3 gap-1 max-w-xs mx-auto mt-4 mb-2';

    // Create 9 cells (3x3 grid)
    for (let i = 0; i < 9; i++) {
      const cell = document.createElement('div');

      // Add buttons at positions 1 (up), 3 (left), 5 (right), 7 (down)
      if (i === 1) { // Up
        const button = document.createElement('button');
        button.className = 'p-1 bg-gray-200 rounded hover:bg-gray-300 w-full';
        button.textContent = '↑';
        button.onclick = () => this.move(0, -1);
        cell.appendChild(button);
      } else if (i === 3) { // Left
        const button = document.createElement('button');
        button.className = 'p-1 bg-gray-200 rounded hover:bg-gray-300 w-full';
        button.textContent = '←';
        button.onclick = () => this.move(-1, 0);
        cell.appendChild(button);
      } else if (i === 5) { // Right
        const button = document.createElement('button');
        button.className = 'p-1 bg-gray-200 rounded hover:bg-gray-300 w-full';
        button.textContent = '→';
        button.onclick = () => this.move(1, 0);
        cell.appendChild(button);
      } else if (i === 7) { // Down
        const button = document.createElement('button');
        button.className = 'p-1 bg-gray-200 rounded hover:bg-gray-300 w-full';
        button.textContent = '↓';
        button.onclick = () => this.move(0, 1);
        cell.appendChild(button);
      }

      controls.appendChild(cell);
    };

    container.appendChild(controls);
    document.body.appendChild(container);

    // Add keyboard controls
    document.addEventListener('keydown', e => {
      const moves = {
        'ArrowLeft': [-1, 0],
        'ArrowRight': [1, 0],
        'ArrowUp': [0, -1],
        'ArrowDown': [0, 1]
      };
      if (moves[e.key]) {
        e.preventDefault();
        this.move(...moves[e.key]);
      }
    });

    this.render();
  }

  getCell(x, y) {
    return document.getElementById(`cell-${x}-${y}`);
  }

  move(dx, dy) {
    const newX = this.player.x + dx;
    const newY = this.player.y + dy;

    // Check bounds
    if (newX < 0 || newX >= 20 || newY < 0 || newY >= 20) return;

    // Check if cell is walkable
    const cell = this.map[newY][newX];
    if (cell === this.CELL_TYPES.STREAM ||
        cell === this.CELL_TYPES.SNORLAX ||
        cell?.type === this.CELL_TYPES.BUILDING) return;

    // Update player position
    const oldX = this.player.x;
    const oldY = this.player.y;
    this.player = { x: newX, y: newY };

    // Update both old and new cells
    this.renderCell(oldX, oldY);
    this.renderCell(newX, newY);

    // Update location text
    this.updateLocationText(newX, newY);
  }

  updateLocationText(x, y) {
    const location = document.getElementById('location');
    const cell = this.map[y][x];

    // first check the current cell
    if (cell?.type === this.CELL_TYPES.BUILDING) {
      location.textContent = `📍 ${this.descriptions[cell.symbol].toLowerCase()}`;
      return;
    } else if (cell?.type === this.CELL_TYPES.KNOWLEDGE_GARDEN) {
      location.textContent = '📍 knowledge garden: a place of learning';
      return;
    } else if (cell?.type === this.CELL_TYPES.PROJECT_GARDEN) {
      location.textContent = '📍 project garden: where ideas grow';
      return;
    } else if (cell?.type === this.CELL_TYPES.FOREST_ENTRANCE) {
      location.textContent = '📍 blog forest: where thoughts take root';
      return;
    } else if (cell === this.CELL_TYPES.FOREST) {
      location.textContent = '📍 blog forest: where thoughts take root';
      return;
    } else if (cell === this.CELL_TYPES.STREAM) {
      location.textContent = '📍 stream: a micro blog';
      return;
    } else if (cell === this.CELL_TYPES.SNORLAX) {
      location.textContent = '📍 sleeping snorlax: zzzzzz...';
      return;
    }

    // then check surrounding cells only if not on a special location
    for (let dy = -1; dy <= 1; dy++) {
      for (let dx = -1; dx <= 1; dx++) {
        const checkY = y + dy;
        const checkX = x + dx;
        if (checkY >= 0 && checkY < 20 && checkX >= 0 && checkX < 20) {
          const nearby = this.map[checkY][checkX];
          if (nearby?.type === this.CELL_TYPES.BUILDING) {
            location.textContent = `📍 ${this.descriptions[nearby.symbol].toLowerCase()}`;
            return;
          }
        }
      }
    }

    // if no special location is found directly under or nearby
    if (this.isNear(x, y, this.CELL_TYPES.STREAM)) {
      location.textContent = '📍 stream: a micro blog';
    } else if (this.isNear(x, y, this.CELL_TYPES.SNORLAX)) {
      location.textContent = '📍 sleeping snorlax: zzzzzz...';
    } else if (this.isNear(x, y, this.CELL_TYPES.FOREST)) {
      location.textContent = '📍 blog forest: where thoughts take root';
    } else {
      location.textContent = 'walking around town...';
    }
  }

  isNear(x, y, type) {
    for (let dy = -1; dy <= 1; dy++) {
      for (let dx = -1; dx <= 1; dx++) {
        const checkY = y + dy;
        const checkX = x + dx;
        if (checkY >= 0 && checkY < 20 && checkX >= 0 && checkX < 20) {
          if (this.map[checkY][checkX] === type) return true;
        }
      }
    }
    return false;
  }

  renderCell(x, y) {
    const cell = this.getCell(x, y);
    if (!cell) return;

    // Clear cell
    cell.innerHTML = '';
    cell.className = 'w-8 h-8 border border-gray-700 relative';

    // Player takes precedence
    if (x === this.player.x && y === this.player.y) {
      cell.className += ' bg-gray-300 flex items-center justify-center';
      cell.textContent = '😎';
      return;
    }

    // Render cell based on type
    const type = this.map[y][x];
    switch (type) {
      case this.CELL_TYPES.PATH:
        cell.className += ' bg-yellow-100';
        break;
      case this.CELL_TYPES.STREAM:
        cell.className += ' bg-blue-300 flex items-center justify-center';
        cell.textContent = '〰️';
        break;
      case this.CELL_TYPES.SNORLAX:
        cell.className += ' bg-transparent overflow-hidden';
        const snorlaxSprite = document.createElement('div');
        snorlaxSprite.className = 'absolute top-0 left-0 w-8 h-8';
        snorlaxSprite.style.backgroundImage = 'url("map-sprites.svg")';
        snorlaxSprite.style.backgroundPosition = '-256px 0';
        snorlaxSprite.style.backgroundSize = '352px 64px';
        snorlaxSprite.style.imageRendering = 'pixelated';
        cell.appendChild(snorlaxSprite);
        break;
      case this.CELL_TYPES.FOREST:
        cell.className += ' bg-green-800 flex items-center justify-center';
        cell.textContent = '🌳';
        break;
      case this.CELL_TYPES.GRASS:
        cell.className += ' bg-green-300';
        break;
      default:
        if (type?.type === this.CELL_TYPES.BUILDING) {
          const spriteX = {
            'H': 0,    // History Museum
            'C': 32,   // Computer Lab
            'R': 64,   // Reading Room
            'A': 96,   // Art Gallery
            'M': 160,  // Memory Circle
            'B': 192,  // Bandstand
            'S': 224,  // Steam Corner
            'P': 128,  // Play Court
            'T': 288,  // Town Square
            'D': 320   // Seaplane Dock
          }[type.symbol];

          cell.className += ' bg-transparent overflow-hidden';
          const sprite = document.createElement('div');
          sprite.className = 'absolute top-0 left-0 w-8 h-8';
          sprite.style.backgroundImage = 'url("map-sprites.svg")';
          sprite.style.backgroundPosition = `-${spriteX}px 0`;
          sprite.style.backgroundSize = '352px 64px';
          sprite.style.imageRendering = 'pixelated';
          cell.appendChild(sprite);
        } else if (type?.type === this.CELL_TYPES.KNOWLEDGE_GARDEN || type?.type === this.CELL_TYPES.PROJECT_GARDEN) {
          const isKnowledge = type.type === this.CELL_TYPES.KNOWLEDGE_GARDEN;
          cell.className += ' bg-green-200 flex items-center justify-center';
          cell.textContent = type.isCenter ? (isKnowledge ? 'K' : 'P') : '🌸';
        } else if (type?.type === this.CELL_TYPES.FOREST_ENTRANCE) {
          cell.className += ' bg-green-700 flex items-center justify-center';
          cell.textContent = 'F';
        }
    }
  }

  render() {
    // Render all cells
    for (let y = 0; y < 20; y++) {
      for (let x = 0; x < 20; x++) {
        this.renderCell(x, y);
      }
    }
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new SimpleTownMap();
});
