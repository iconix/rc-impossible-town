/**
 * A top-down RPG-style game using Phaser 3
 * Based on Post 1 of https://github.com/mikewesthad/phaser-3-tilemap-blog-posts
 *
 * Asset Credits:
 * - Tuxemon: https://github.com/Tuxemon/Tuxemon
 */

/// <reference path='phaser.d.ts' />

/**
 * @typedef {Object} GameState
 * @property {Phaser.Cameras.Controls.FixedKeyControl|null} controls - Camera controls
 * @property {Phaser.Types.Input.Keyboard.CursorKeys|null} cursors - Keyboard cursors
 * @property {Phaser.Physics.Arcade.Sprite|null} player - Player sprite
 * @property {'player'|'camera'} controlMode - Current control mode
 * @property {Phaser.GameObjects.Graphics|null} debugGraphics - Debug graphics object
 * @property {boolean} debugMode - Whether debug mode is enabled
 * @property {Phaser.GameObjects.Text|null} helpText - Help text display
 */


class GameScene extends Phaser.Scene
{
    constructor() {
        super({ key: 'GameScene' });

        /** @type {GameState} */
        this.gameState = {
            controls: null,
            cursors: null,
            player: null,
            controlMode: 'player',  // 'player' or 'camera'
            debugGraphics: null,
            debugMode: false,
            helpText: null,
        };

        // Constants
        this.PLAYER_SPEED = 175;
        this.CAMERA_SPEED = 0.5;
    }

    // runs once, loads up assets like images and audio
    preload ()
    {
        // load map assets
        this.load.image('tiles', 'public/assets/tilesets/tuxemon-sample-32px-extruded.png');
        this.load.tilemapTiledJSON('map', 'public/assets/tilemaps/tuxemon-town.json');

        // load character sprite atlas
        // an atlas is a way to pack multiple images together into one texture.
        // using it to load all the player animations (walking left, walking right, etc.) in one image.
        // for more info see: https://labs.phaser.io/view.html?src=src/animation/texture%20atlas%20animation.js
        // if you don't use an atlas, you can do the same thing with a spritesheet, see:
        //  https://labs.phaser.io/view.html?src=src/animation/single%20sprite%20sheet.js
        this.load.atlas('atlas', 'public/assets/atlas/atlas.png', 'public/assets/atlas/atlas.json');
    }

    // runs once, after all assets in preload are loaded
    create ()
    {
        const map = this.createMap();

        // set up the arrows to control the camera
        this.gameState.cursors = this.input.keyboard?.createCursorKeys() || null;

        this.createCameraPan(map);
        this.createPlayer(map);
        this.createPlayerAnimations();
        this.setupControlToggle();
        this.setupDebugFeatures(map);

        if (this.gameState.player && this.gameState.controlMode === 'player') {
            this.cameras.main.startFollow(this.gameState.player);
        }
    }

    // runs once per frame for the duration of the scene
    update(time, delta) {
        if (this.gameState.controlMode === 'player') {
            this.updatePlayer();
        } else {
            this.updateCameraPan(delta);
        }
    }

    createMap() {
        const map = this.make.tilemap({ key: 'map' });

        // parameters: name you gave the tileset in Tiled, key of the tileset image in phaser's cache
        // (i.e. the name you used in preload)
        const tileset = map.addTilesetImage('tuxemon-sample-32px-extruded', 'tiles');

        // parameters: layer name (or index) from Tiled, tileset, x, y
        const belowLayer = map.createLayer('Below Player', tileset, 0, 0);
        const worldLayer = map.createLayer('World', tileset, 0, 0);
        const aboveLayer = map.createLayer('Above Player', tileset, 0, 0);

        if (!belowLayer || !worldLayer || !aboveLayer) {
            console.error('failed to create map layers');
            return;
        }

        // By default, everything gets depth sorted on the screen in the order we created things. Here, we
        // want the 'Above Player' layer to sit on top of the player, so we explicitly give it a depth.
        // Higher depths will sit on top of lower depth objects.
        aboveLayer.setDepth(10);

        // marks tiles as collide-able in tilemap
        worldLayer.setCollisionByProperty({ collides: true });

        return map;
    }

    createCameraPan(map) {
        // phaser supports multiple cameras, but this is the default camera
        const camera = this.cameras.main;

        if (this.gameState.cursors) {
            this.gameState.controls = new Phaser.Cameras.Controls.FixedKeyControl({
                camera: camera,
                left: this.gameState.cursors.left,
                right: this.gameState.cursors.right,
                up: this.gameState.cursors.up,
                down: this.gameState.cursors.down,
                speed: this.CAMERA_SPEED,
            });
        } else {
            console.log('woops! no cursor keys... something went wrong.');
        }

        // constrain the camera so that it isn't allowed to move outside the width/height of tilemap
        camera.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
    }

    createPlayer(map) {
        const worldLayer = map.getLayer('World').tilemapLayer;

        // phaser supports multiple cameras, but this is the default camera
        const camera = this.cameras.main;

        // object layers in Tiled let you embed extra info into a map - like a spawn point or custom
        // collision shapes. in the tmx file, there's an object layer with a point named 'Spawn Point'
        const spawnPoint = map.findObject('Objects', (obj) => obj.name === 'Spawn Point');

        this.gameState.player = this.physics.add.sprite(spawnPoint.x || 400, spawnPoint.y || 350, 'atlas', 'misa-front');

        if (!this.gameState.player) {
            console.error('failed to create player sprite');
            return;
        }

        // this will watch the player and worldLayer every frame to check for collisions
        this.physics.add.collider(this.gameState.player, worldLayer);

        camera.setBounds(0, 0, map.widthInPixels, map.heightInPixels);

        this.createHelpText();
    }

    createPlayerAnimations() {
        const animations = [
            {
              key: 'misa-left-walk',
              prefix: 'misa-left-walk.',
              start: 0,
              end: 3
            },
            {
              key: 'misa-right-walk',
              prefix: 'misa-right-walk.',
              start: 0,
              end: 3
            },
            {
              key: 'misa-front-walk',
              prefix: 'misa-front-walk.',
              start: 0,
              end: 3
            },
            {
              key: 'misa-back-walk',
              prefix: 'misa-back-walk.',
              start: 0,
              end: 3
            }
          ];

        animations.forEach(({ key, prefix, start, end }) => {
            // create the player's walking animations from the texture atlas.
            // these are stored in the global animation manager so any sprite can access them.
            this.anims.create({
                key,
                frames: this.anims.generateFrameNames('atlas', {
                    prefix,
                    start,
                    end,
                    zeroPad: 3
                }),
                frameRate: 10,
                repeat: -1
            });
        });
    }

    createHelpText() {
        // create text that has a 'fixed' position on the screen
        // put in gameState so we can update it later
        this.gameState.helpText = this.add.text(16, 16, '', {
            font: '18px monospace',
            color: '#000000',
            padding: { x: 20, y: 10 },
            backgroundColor: '#ffffff'
        })
        .setScrollFactor(0)
        .setDepth(30);

        this.updateHelpText();
      }

    updateCameraPan(delta) {
        if (this.gameState.controls) {
            // apply the controls to the camera each update tick of the game
            this.gameState.controls.update(delta);
        }
    }

    updatePlayer() {
        if (!this.gameState.player || !this.gameState.cursors) return;

        const { player, cursors } = this.gameState;

        /** @type {Phaser.Physics.Arcade.Body} */
        // @ts-ignore
        const body = player.body;

        const prevVelocity = body?.velocity.clone();

        // stop any previous movement from the last frame
        body?.setVelocity(0);

        // horizontal movement
        if (cursors.left.isDown) {
            body?.setVelocityX(-this.PLAYER_SPEED);
        } else if (cursors.right.isDown) {
            body?.setVelocityX(this.PLAYER_SPEED);
        }

        // vertical movement
        if (cursors.up.isDown) {
            body?.setVelocityY(-this.PLAYER_SPEED);
        } else if (cursors.down.isDown) {
            body?.setVelocityY(this.PLAYER_SPEED);
        }

        // normalize and scale the velocity so that player can't move faster along a diagonal
        body?.velocity.normalize().scale(this.PLAYER_SPEED);

        this.updatePlayerAnimation(prevVelocity);
    }

    updatePlayerAnimation(prevVelocity) {
        if (!this.gameState.player || !this.gameState.cursors) return;

        const { player, cursors } = this.gameState;

        // update the animation last and give left/right animations precedence over up/down animations
        if (cursors.left.isDown) {
            player.anims.play('misa-left-walk', true);
        } else if (cursors.right.isDown) {
            player.anims.play('misa-right-walk', true);
        } else if (cursors.up.isDown) {
            player.anims.play('misa-back-walk', true);
        } else if (cursors.down.isDown) {
            player.anims.play('misa-front-walk', true);
        } else {
            player.anims.stop();

            // set idle frame based on previous movement
            if (prevVelocity.x < 0) player.setTexture('atlas', 'misa-left');
            else if (prevVelocity.x > 0) player.setTexture('atlas', 'misa-right');
            else if (prevVelocity.y < 0) player.setTexture('atlas', 'misa-back');
            else if (prevVelocity.y > 0) player.setTexture('atlas', 'misa-front');
        }
    }

    updateHelpText() {
        const modeText = this.gameState.controlMode === 'player'
        ? 'Arrow keys to move'
        : 'Arrow keys to pan camera';

        const helpText = `${modeText}\nPress 'C' to switch mode\nPress 'D' to toggle hitboxes`;

        this.gameState.helpText?.setText(helpText);
    }

    setupControlToggle() {
        this.input.keyboard?.on('keydown-C', () => {
          this.gameState.controlMode = this.gameState.controlMode === 'player' ? 'camera' : 'player';

          const camera = this.cameras.main;

          if (this.gameState.controlMode === 'player' && this.gameState.player) {
                // switch to player mode
                camera.startFollow(this.gameState.player);
                this.gameState.player.active = true;
                this.gameState.player.setVisible(true);
          } else if (this.gameState.player) {
                // switch to camera mode
                camera.stopFollow();
                this.gameState.player.active = false;
          }

          // update help text
          this.updateHelpText();
        });
      }

    setupDebugFeatures(map) {
        const worldLayer = map.getLayer('World').tilemapLayer;

        // create (but don't enable) debug graphics
        this.gameState.debugGraphics = this.add.graphics().setAlpha(0.75).setDepth(20);

        this.input.keyboard?.on('keydown-D', () => {
            this.gameState.debugMode = !this.gameState.debugMode;

            if (this.gameState.debugMode) {
                // turn on physics debugging to show player's hitbox
                this.physics.world.createDebugGraphic();

                // create worldLayer collision graphic above the player, but below the help text
                worldLayer.renderDebug(this.gameState.debugGraphics, {
                    tileColor: null, // color of non-colliding tiles
                    collidingTileColor: new Phaser.Display.Color(243, 134, 48, 255), // color of colliding tiles
                    faceColor: new Phaser.Display.Color(40, 39, 37, 255), // color of colliding face edges
                });
            } else {
                // clear debug graphics
                this.physics.world.debugGraphic.destroy();
                this.gameState.debugGraphics?.clear();
            }
        });
    }
}

const config = {
    type: Phaser.AUTO,          // which renderer to use
    width: 800,                 // canvas width in pixels
    height: 600,                // canvas height in pixels
    parent: 'game-container',   // id of the dom element to add the canvas to
    pixelArt: true,
    scene: GameScene,
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { x: 0, y: 0 }   // top down game, so no gravity
        }
    }
};

const game = new Phaser.Game(config);
