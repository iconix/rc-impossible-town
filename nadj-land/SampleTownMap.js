/**
 * A top-down RPG-style game using Phaser 3
 *
 * Asset Credits in public\assets\CREDITS.md
 */

/// <reference path='phaser.d.ts' />

/**
 * @typedef {Object} TownState
 * @property {Phaser.Cameras.Controls.FixedKeyControl|null} controls - Camera controls
 * @property {Phaser.Types.Input.Keyboard.CursorKeys|null} cursors - Keyboard cursors
 * @property {Phaser.Physics.Arcade.Sprite|null} player - Player sprite
 * @property {'player'|'camera'} controlMode - Current control mode
 * @property {Phaser.GameObjects.Graphics|null} debugGraphics - Debug graphics object
 * @property {boolean} debugMode - Whether debug mode is enabled
 * @property {Phaser.GameObjects.Text|null} helpText - Help text display
 * @property {'front'|'back'|'left'|'right'} lastDirection - Last direction player was facing
 * @property {boolean} isPointerDown - Whether pointer is currently being held down
 * @property {Phaser.Math.Vector2} pointerTarget - Target position for pointer movement
 */


class TownScene extends Phaser.Scene
{
    constructor() {
        super({ key: 'TownScene' });

        /** @type {TownState} */
        this.townState = {
            controls: null,
            cursors: null,
            player: null,
            controlMode: 'player',  // 'player' or 'camera'
            debugGraphics: null,
            debugMode: false,
            helpText: null,
            lastDirection: 'front',
            isPointerDown: false,
            pointerTarget: new Phaser.Math.Vector2(),
        };

        // Constants
        this.PLAYER_SPEED = 100;
        this.CAMERA_SPEED = 0.5;
        this.POINTER_DEADZONE = 10; // minimum distance for pointer movement
        this.isEnteringDoor = false;
    }

    // runs once, loads up assets like images and audio
    preload ()
    {
        // load tilemap and tileset assets
        this.load.tilemapTiledJSON('town', 'public/assets/tilemaps/sample-town.tmj');
        this.load.atlas('town-objects-32',
            'public/assets/spritesheets/pixel-quest-sample-town-32-repack.png',
            'public/assets/spritesheets/pixel-quest-sample-town-32-repack-atlas.json'
        );
        this.load.atlas('town-objects-16',
            'public/assets/spritesheets/pixel-quest-sample-town-16.png',
            'public/assets/spritesheets/pixel-quest-sample-town-16-atlas.json'
        );

        // load character sprite atlas
        this.load.atlas('lenora',
            'public/assets/spritesheets/lenora.png',
            'public/assets/spritesheets/lenora-atlas.json'
        );
    }

    // runs once, after all assets in preload are loaded
    create (data)
    {
        const map = this.createMap();

        const layers = [
            map?.getLayer('Ground')?.tilemapLayer,
            map?.getLayer('Ground Decoration')?.tilemapLayer,
            map?.getLayer('World')?.tilemapLayer,
            map?.getLayer('Above World')?.tilemapLayer
        ];

        layers.forEach(layer => {
            if (layer) {
                // force tiles to snap to pixel grid
                layer.setPosition(Math.floor(layer.x), Math.floor(layer.y));
            }
        });

        // set up the arrows to control the camera
        this.townState.cursors = this.input.keyboard?.createCursorKeys() || null;

        this.createCameraPan(map);
        this.createPlayer(map);
        this.createPlayerAnimations();
        this.setupPointerControls();
        this.setupDoorInteractions();
        this.setupControlToggle();
        this.setupDebugFeatures(map);

        if (this.townState.player && this.townState.controlMode === 'player') {
            this.cameras.main.startFollow(this.townState.player);
        }

        this.cameras.main.roundPixels = true;
        this.cameras.main.setZoom(SCALE_FACTOR);
        this.cameras.main.scrollX = Math.floor(this.cameras.main.scrollX);
        this.cameras.main.scrollY = Math.floor(this.cameras.main.scrollY);

        const uiCamera = this.cameras.add(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
        uiCamera.setScroll(0, 0);
        uiCamera.ignore(this.children.list.filter(obj => obj !== this.townState.helpText));

        if (this.townState.helpText) {
            // make main camera ignore the help text
            this.cameras.main.ignore(this.townState.helpText)
        }

        // check if we're coming from interior scene
        if (this.doors && data && data.fromInterior && data.doorPosition) {
            // find the door at this position
            const door = Array.from(this.doors.values()).find(d =>
                d.x === data.doorPosition.x &&
                d.y === data.doorPosition.y
            );

            if (door) {
                // wait a frame to ensure everything is initialized
                this.time.delayedCall(0, () => {
                    this.handleExitTransition(door);
                });
            }
        }

        this.scale.on('resize', () => { this.handleResize(map) }, this);
    }

    // runs once per frame for the duration of the scene
    update(time, delta) {
        if (this.townState.controlMode === 'player') {
            this.updatePlayer();
        } else {
            this.updateCameraPan(delta);
        }
    }

    createMap() {
        const map = this.make.tilemap({ key: 'town' });

        // parameters: name you gave the tileset in Tiled, key of the tileset image in phaser's cache
        // (i.e. the name you used in preload)
        const tileset16 = map.addTilesetImage('pixel-quest-sample-town-16', 'town-objects-16');
        const tileset32 = map.addTilesetImage('pixel-quest-sample-town-32-repack', 'town-objects-32');

        if (!tileset16 || !tileset32) {
            console.error('failed to add tileset images');
            return;
        }

        // parameters: layer name (or index) from Tiled, tileset
        const groundLayer = map.createLayer('Ground', [tileset16, tileset32])
            ?.setScale(1)
            .setPipeline('TextureTintPipeline');
        const groundDecorationLayer = map.createLayer('Ground Decoration', [tileset16, tileset32])
            ?.setScale(1)
            .setPipeline('TextureTintPipeline');
        const worldLayer = map.createLayer('World', [tileset16, tileset32])
            ?.setScale(1)
            .setPipeline('TextureTintPipeline');
        const aboveWorldLayer = map.createLayer('Above World', [tileset16, tileset32])
            ?.setScale(1)
            .setPipeline('TextureTintPipeline');

        // special way to create a layer from an object layer
        const objectLayer = map.getObjectLayer('Objects');

        if (!groundLayer || !groundDecorationLayer || !worldLayer || !aboveWorldLayer || !objectLayer) {
            console.error('failed to create map layers');
            return;
        }

        this.createGameObjectAnimations();
        this.createGameObjects(map, objectLayer);

        // By default, everything gets depth sorted on the screen in the order we created things. Here, we
        // want the 'Above World' layer to sit on top of the player, so we explicitly give it a depth.
        // Higher depths will sit on top of lower depth objects.
        aboveWorldLayer.setDepth(10);

        // marks tiles as collide-able in tilemap
        worldLayer.setCollisionByProperty({ collides: true });

        return map;
    }

    createGameObjects(map, objectLayer) {
        this.objectGroup = this.add.group();
        this.doors = new Map();

        // create game objects from the object layer
        objectLayer.objects.forEach(object => {
            // get custom Tiled properties
            const spriteName = object.properties?.find(p => p.name === 'sprite')?.value;
            const type = object.properties?.find(p => p.name === 'type')?.value;
            const atlas = object.properties?.find(p => p.name === 'atlas')?.value || 'town-objects-32';

            if (!spriteName) {
                console.warn(`Object ${object.id} has no sprite property`);
                return;
            }

            if (type === 'closed_door') {
                const door = this.add.sprite(
                    object.x + (object.width / 2),
                    object.y - (object.height / 2),
                    atlas,
                    spriteName
                );

                this.objectGroup?.add(door);
                door.objectId = object.id;
                door.isDoor = true;  // flag to identify doors

                // store doors for later interaction setup
                this.doors?.set(door.objectId, door);

                // set depth to match the World layer
                const worldLayer = map.getLayer('World').tilemapLayer;
                door.setDepth(worldLayer.depth);

                return;
            }

            // handle remaining non-door objects

            // validate that the sprite exists in our atlas
            const validSprites = this.textures.get(atlas).getFrameNames();

            if (!validSprites.includes(spriteName)) {
                console.warn(`Invalid sprite name: ${spriteName}`);
                return;
            }

            // create sprite at the correct position
            // note: Tiled position is bottom-left, Phaser is top-left
            const sprite = this.add.sprite(
                object.x + (object.width / 2),  // center the sprite horizontally
                object.y - (object.height / 2), // center the sprite vertically
                atlas,
                spriteName
            );

            // get collision property from Tiled
            const collides = object.properties?.find(p => p.name === 'collides')?.value ?? false;

            // enable physics and set up collision if needed
            if (collides) {
                this.physics.world.enable(sprite);
                sprite.body.setImmovable(true);  // makes the object not move when collided with
            }

            // add to our group
            this.objectGroup?.add(sprite);

            // store the original object id if needed
            sprite.objectId = object.id;

            if (spriteName === 'left_chimney' || spriteName == 'right_chimney') {
                // make sure the chimneys are really high up
                sprite.setDepth(20);
            }

            // start animation if this sprite type is animated
            this.startAnimationIfNeeded(sprite, spriteName);

            // copy over all custom properties from Tiled
            if (object.properties) {
                object.properties.forEach(prop => {
                    sprite[prop.name] = prop.value;
                });
            }

            // make interactive if needed
            // sprite.setInteractive();
            // sprite.on('pointerdown', () => {
            //     this.handleItemClick(sprite);
            // });

            // // optional: add custom behavior based on item type
            // this.setupItemBehavior(sprite, object);
        });
    }

    createGameObjectAnimations() {
        if (!this.anims.exists('fountain_anim')) {
            this.anims.create({
                key: 'fountain_anim',
                frames: [
                    { key: 'town-objects-32', frame: 'fountain_1' },
                    { key: 'town-objects-32', frame: 'fountain_2' },
                    { key: 'town-objects-32', frame: 'fountain_3' },
                    { key: 'town-objects-32', frame: 'fountain_4' }
                ],
                frameRate: 10, // 100ms per frame = 10fps
                repeat: -1
            });
        }

        // left chimney animation (6 frames, 100ms each)
        if (!this.anims.exists('left_chimney_anim')) {
            this.anims.create({
                key: 'left_chimney_anim',
                frames: [
                    { key: 'town-objects-32', frame: 'left_chimney_1' },
                    { key: 'town-objects-32', frame: 'left_chimney_2' },
                    { key: 'town-objects-32', frame: 'left_chimney_3' },
                    { key: 'town-objects-32', frame: 'left_chimney_4' },
                    { key: 'town-objects-32', frame: 'left_chimney_5' },
                    { key: 'town-objects-32', frame: 'left_chimney_6' }
                ],
                frameRate: 10, // 100ms per frame = 10fps
                repeat: -1
            });
        }

        // right chimney animation (6 frames, 100ms each)
        if (!this.anims.exists('right_chimney_anim')) {
            this.anims.create({
                key: 'right_chimney_anim',
                frames: [
                    { key: 'town-objects-32', frame: 'right_chimney_1' },
                    { key: 'town-objects-32', frame: 'right_chimney_2' },
                    { key: 'town-objects-32', frame: 'right_chimney_3' },
                    { key: 'town-objects-32', frame: 'right_chimney_4' },
                    { key: 'town-objects-32', frame: 'right_chimney_5' },
                    { key: 'town-objects-32', frame: 'right_chimney_6' }
                ],
                frameRate: 10, // 100ms per frame = 10fps
                repeat: -1
            });
        }

        // door animations
        if (!this.anims.exists('door_open')) {
            this.anims.create({
                key: 'door_open',
                frames: [
                    { key: 'town-objects-16', frame: 'wooden_door_closed' },
                    { key: 'town-objects-16', frame: 'wooden_door_open' }
                ],
                frameRate: 10,
                repeat: 0  // play once and stay open
            });
        }

        if (!this.anims.exists('door_close')) {
            this.anims.create({
                key: 'door_close',
                frames: [
                    { key: 'town-objects-16', frame: 'wooden_door_open' },
                    { key: 'town-objects-16', frame: 'wooden_door_closed' }
                ],
                frameRate: 10,
                repeat: 0  // play once and stay closed
            });
        }
    }

    startAnimationIfNeeded(sprite, spriteName) {
        const animationMap = {
            'fountain': 'fountain_anim',
            'left_chimney': 'left_chimney_anim',
            'right_chimney': 'right_chimney_anim'
        };

        if (animationMap[spriteName]) {
            sprite.play(animationMap[spriteName]);
        }
    }

    setupPointerControls() {
        this.input.on('pointerdown', (pointer) => {
            if (this.townState.controlMode === 'player') {
                this.townState.isPointerDown = true;
                const worldPoint = this.cameras.main.getWorldPoint(pointer.x, pointer.y);
                this.townState.pointerTarget.set(worldPoint.x, worldPoint.y);
            }
        });

        this.input.on('pointermove', (pointer) => {
            if (this.townState.isPointerDown && this.townState.controlMode === 'player') {
                const worldPoint = this.cameras.main.getWorldPoint(pointer.x, pointer.y);
                this.townState.pointerTarget.set(worldPoint.x, worldPoint.y);
            }
        });

        this.input.on('pointerup', () => {
            this.townState.isPointerDown = false;
        });
    }

    setupDoorInteractions() {
        if (!this.townState.player) return;

        this.doors?.forEach(door => {
            // create trigger zone in front of door
            const triggerZone = this.add.zone(
                door.x,
                door.y + 16,
                16,
                16
            );
            this.physics.world.enable(triggerZone);

            // add overlap with player
            this.physics.add.overlap(
                this.townState.player,
                triggerZone,
                () => this.handleDoorEnter(door),
                () => !this.isEnteringDoor,
                this
            );
        });
    }

    handleDoorEnter(door) {
        if (this.isEnteringDoor) return;
        this.isEnteringDoor = true;

        // store door position for exit
        this.exitPosition = { x: door.x, y: door.y };

        // disable player input
        if (this.townState.player) {

            /** @type {Phaser.Physics.Arcade.Body} */
            // @ts-ignore
            const body = this.townState.player.body;

            // clear any existing velocity
            body.setVelocity(0);

            // disable physics movement
            this.townState.player.setImmovable(true);

            // stop any ongoing animations and set to idle
            this.townState.player.anims.stop();
            this.townState.player.anims.play(`lenora-back`, true);
        }

         // first center the player horizontally on the door
        this.tweens.add({
            targets: this.townState.player,
            x: door.x,
            duration: 200,
            onComplete: () => {
                // then play door opening animation
                door.play('door_open').on('animationcomplete', () => {
                    // then move player through the door
                    this.tweens.add({
                        targets: this.townState.player,
                        y: door.y,  // move to door position
                        alpha: 0,
                        duration: 500,
                        onComplete: () => {
                            // finally, close door after player enters
                            door.play('door_close');

                            // clean up before switching scenes
                            this.isEnteringDoor = false;

                            this.handleInteriorTransition();
                        }
                    });
                });
            }
        });
    }

    handleInteriorTransition() {
        // switch to a new scene for the interior
        this.scene.start('InteriorScene');
    }

    handleExitTransition(doorObj) {
        if (!this.townState.player) return;

        // reset any existing animations
        doorObj.anims.stop();

        // position player inside door, invisible
        this.townState.player.setPosition(doorObj.x, doorObj.y);
        this.townState.player.setAlpha(0);
        this.townState.player.setImmovable(true);
        this.isEnteringDoor = true;

        // add new completion handler
        doorObj.once('animationcomplete', () => {
            this.tweens.add({
                targets: this.townState.player,
                y: doorObj.y + 32,
                alpha: 1,
                duration: 500,
                onComplete: () => {
                    // clear any existing listeners again
                    doorObj.removeAllListeners('animationcomplete');
                    // add new completion handler for closing
                    doorObj.once('animationcomplete', () => {
                        this.townState.player?.setImmovable(false);
                        this.isEnteringDoor = false;
                    });
                    doorObj.play('door_close');
                }
            });
        });

        doorObj.play('door_open');
    }

    handleResize(map) {
        // handle viewport resizing
        if (this.cameras.main) {
            // ensure camera position is on pixel boundaries
            this.cameras.main.scrollX = Math.floor(this.cameras.main.scrollX);
            this.cameras.main.scrollY = Math.floor(this.cameras.main.scrollY);

            // update all layer positions
            const layers = map?.layers || [];
            layers.forEach(layer => {
                if (layer.tilemapLayer) {
                    layer.tilemapLayer.setPosition(
                        Math.floor(layer.tilemapLayer.x),
                        Math.floor(layer.tilemapLayer.y)
                    );
                }
            });
        }
    }

    createCameraPan(map) {
        // phaser supports multiple cameras, but this is the default camera
        const camera = this.cameras.main;

        if (this.townState.cursors) {
            this.townState.controls = new Phaser.Cameras.Controls.FixedKeyControl({
                camera: camera,
                left: this.townState.cursors.left,
                right: this.townState.cursors.right,
                up: this.townState.cursors.up,
                down: this.townState.cursors.down,
                speed: this.CAMERA_SPEED,
            });
        } else {
            console.log('woops! no cursor keys... something went wrong.');
        }

        // constrain the camera so that it isn't allowed to move outside the width/height of tilemap (320x224)
        camera.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
    }

    createPlayer(map) {
        const worldLayer = map.getLayer('World').tilemapLayer;

        // phaser supports multiple cameras, but this is the default camera
        const camera = this.cameras.main;

        // object layers in Tiled let you embed extra info into a map - like a spawn point or custom
        // collision shapes. in the tmx file, there's an object layer with a point named 'Spawn Point'
        const spawnPoint = map.findObject('Objects', (obj) => obj.name === 'Spawn Point');

        this.townState.player = this.physics.add.sprite(spawnPoint.x || 400, spawnPoint.y || 350, 'lenora');

        if (!this.townState.player) {
            console.error('failed to create player sprite');
            return;
        }

        // smaller map, make player smaller
        this.townState.player.setScale(0.4, 0.4);

        // set a small hitbox to allow player to move through tighter spaces
        this.townState.player.body?.setSize(18, 18);

        // center the hitbox within the sprite
        // offset is measured from top-left of the sprite
        this.townState.player.body?.setOffset(22, 44);

        // set initial facing direction
        this.townState.lastDirection = 'front';
        this.townState.player.anims.play('lenora-front', true);

        // this will watch the player and worldLayer every frame to check for collisions
        this.physics.add.collider(this.townState.player, worldLayer);
        this.physics.add.collider(this.townState.player, this.objectGroup);

        camera.setBounds(0, 0, map.widthInPixels, map.heightInPixels);

        this.createHelpText();
    }

    createPlayerAnimations() {
        const animations = [
            {
                key: 'lenora-front-walk',
                frames: [
                    { key: 'lenora', frame: 'front-walk-1' },
                    { key: 'lenora', frame: 'front-walk-2' },
                    { key: 'lenora', frame: 'front-walk-3' }
                ]
            },
            {
                key: 'lenora-left-walk',
                frames: [
                    { key: 'lenora', frame: 'left-walk-1' },
                    { key: 'lenora', frame: 'left-walk-2' },
                    { key: 'lenora', frame: 'left-walk-3' }
                ]
            },
            {
                key: 'lenora-right-walk',
                frames: [
                    { key: 'lenora', frame: 'right-walk-1' },
                    { key: 'lenora', frame: 'right-walk-2' },
                    { key: 'lenora', frame: 'right-walk-3' }
                ]
            },
            {
                key: 'lenora-back-walk',
                frames: [
                    { key: 'lenora', frame: 'back-walk-1' },
                    { key: 'lenora', frame: 'back-walk-2' },
                    { key: 'lenora', frame: 'back-walk-3' }
                ]
            }
        ];

        const idling = [
            {
                key: 'lenora-front',
                frame: 'front-idle'
            },
            {
                key: 'lenora-left',
                frame: 'left-idle'
            },
            {
                key: 'lenora-right',
                frame: 'right-idle'
            },
            {
                key: 'lenora-back',
                frame: 'back-idle'
            }
        ];

        animations.forEach(({ key, frames }) => {
            if (!this.anims.exists(key)) {
                // create walking animations using atlas frames
                // these are stored in the global animation manager so any sprite can access them
                this.anims.create({
                    key,
                    frames,
                    frameRate: 10,
                    repeat: -1
                });
            }
        });

        idling.forEach(({ key, frame }) => {
            if (!this.anims.exists(key)) {
                // create idle animations using atlas frames
                this.anims.create({
                    key,
                    frames: [{ key: 'lenora', frame }],
                    frameRate: 10
                });
            }
        });
    }

    createHelpText() {
        // create text that has a 'fixed' position on the screen
        // put in townState so we can update it later
        this.townState.helpText = this.add.text(16, 16, '', {
            font: '12px monospace',
            color: '#000000',
            padding: { x: 20, y: 10 },
            backgroundColor: '#ffffff'
        })
        .setScrollFactor(0)
        .setDepth(30);

        this.updateHelpText();
      }

    updateCameraPan(delta) {
        if (this.townState.controls) {
            // apply the controls to the camera each update tick of the game
            this.townState.controls.update(delta);
        }
    }

    updatePlayer() {
        if (!this.townState.player || !this.townState.cursors || this.isEnteringDoor) return;

        const { player, cursors, isPointerDown, pointerTarget } = this.townState;

        /** @type {Phaser.Physics.Arcade.Body} */
        // @ts-ignore
        const body = player.body;

        // stop any previous movement from the last frame
        body?.setVelocity(0);

        // handle keyboard input
        if (cursors) {
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
        }

        // handle pointer input
        if (isPointerDown) {
            const distance = Phaser.Math.Distance.Between(
                player.x, player.y,
                pointerTarget.x, pointerTarget.y
            );

            if (distance > this.POINTER_DEADZONE) {
                // calculate direction to target
                const angle = Phaser.Math.Angle.Between(
                    player.x, player.y,
                    pointerTarget.x, pointerTarget.y
                );

                // convert angle to velocity
                body?.setVelocity(
                    Math.cos(angle) * this.PLAYER_SPEED,
                    Math.sin(angle) * this.PLAYER_SPEED
                );
            }
        }

        // normalize and scale the velocity so that player can't move faster along a diagonal
        body?.velocity.normalize()?.scale(this.PLAYER_SPEED);

        this.updatePlayerAnimation();
    }

    updatePlayerAnimation() {
        if (!this.townState.player || !this.townState.cursors) return;

        const { player } = this.townState;

        /** @type {Phaser.Physics.Arcade.Body} */
        // @ts-ignore
        const body = player.body;

        // only play walk animations if actually moving
        if (Math.abs(body.velocity.x) > 0 || Math.abs(body.velocity.y) > 0) {
            // determine primary direction based on velocity magnitudes
            const absVelX = Math.abs(body.velocity.x);
            const absVelY = Math.abs(body.velocity.y);

            // update the animation last and give left/right animations precedence over up/down animations
            if (absVelX > absVelY) {
                // horizontal movement is dominant
                if (body.velocity.x < 0) {
                    this.townState.lastDirection = 'left';
                    player.anims.play('lenora-left-walk', true);
                } else {
                    this.townState.lastDirection = 'right';
                    player.anims.play('lenora-right-walk', true);
                }
            } else {
                // vertical movement is dominant
                if (body.velocity.y < 0) {
                    this.townState.lastDirection = 'back';
                    player.anims.play('lenora-back-walk', true);
                } else {
                    this.townState.lastDirection = 'front';
                    player.anims.play('lenora-front-walk', true);
                }
            }
        } else {
            player.anims.stop();

            // set idle frame based on last direction
            player.anims.play(`lenora-${this.townState.lastDirection}`);
        }
    }

    updateHelpText() {
        const modeText = this.townState.controlMode === 'player'
        ? 'Arrow keys or hold pointer to move'
        : 'Arrow keys to pan camera';

        const helpText = `${modeText}\nPress 'C' to switch mode\nPress 'D' to toggle hitboxes`;

        this.townState.helpText?.setText(helpText);
    }

    setupControlToggle() {
        this.input.keyboard?.on('keydown-C', () => {
          this.townState.controlMode = this.townState.controlMode === 'player' ? 'camera' : 'player';

          const camera = this.cameras.main;

          if (this.townState.controlMode === 'player' && this.townState.player) {
                // switch to player mode
                camera.startFollow(this.townState.player);
                this.townState.player.active = true;
                this.townState.player.setVisible(true);
          } else if (this.townState.player) {
                // switch to camera mode
                camera.stopFollow();
                this.townState.player.active = false;
          }

          // update help text
          this.updateHelpText();
        });
      }

    setupDebugFeatures(map) {
        const worldLayer = map.getLayer('World').tilemapLayer;

        // create (but don't enable) debug graphics
        this.townState.debugGraphics = this.add.graphics().setAlpha(0.75).setDepth(20);

        this.input.keyboard?.on('keydown-D', () => {
            this.townState.debugMode = !this.townState.debugMode;

            if (this.townState.debugMode) {
                // turn on physics debugging to show player's hitbox
                this.physics.world.createDebugGraphic();

                // create worldLayer collision graphic above the player, but below the help text
                worldLayer.renderDebug(this.townState.debugGraphics, {
                    tileColor: null, // color of non-colliding tiles
                    collidingTileColor: new Phaser.Display.Color(243, 134, 48, 255), // color of colliding tiles
                    faceColor: new Phaser.Display.Color(40, 39, 37, 255), // color of colliding face edges
                });
            } else {
                // clear debug graphics
                this.physics.world.debugGraphic.destroy();
                this.townState.debugGraphics?.clear();
            }
        });
    }
}


class InteriorScene extends Phaser.Scene {
    constructor() {
        super({ key: 'InteriorScene' });
    }

    preload() {
        // load a web font
        this.load.script('webfont', 'https://ajax.googleapis.com/ajax/libs/webfont/1.6.26/webfont.js');
    }

    create() {
        // get door position from TownScene if available
        const townScene = this.scene.get('TownScene');
        this.lastDoorPosition = townScene.exitPosition;

        this.cameras.main.setBackgroundColor('#000000');

        // load fonts before creating text
        // @ts-ignore
        WebFont.load({
            google: {
                families: ['UnifrakturMaguntia', 'Playfair Display']  // gothic font for title, serif for subtitle
            },
            active: () => {
                // create decorative border
                const graphics = this.add.graphics();
                graphics.lineStyle(4, 0xFFFFFF);
                graphics.strokeRect(100, 100, 600, 360);

                const title = this.add.text(400, 200, 'Interior Room', {
                    fontFamily: 'UnifrakturMaguntia',
                    fontSize: '64px',
                    color: '#FFFFFF',
                });
                title.setOrigin(0.5);
                title.setAlpha(0);

                // fade in main title first
                this.tweens.add({
                    targets: title,
                    alpha: 1,
                    duration: 2000,
                    ease: 'Power1'
                });

                const subtitle = this.add.text(400, 300, 'As dark as the interior of my soul...', {
                    fontFamily: 'Playfair Display',
                    fontSize: '24px',
                    color: '#CCCCCC',
                    fontStyle: 'italic'
                });
                subtitle.setOrigin(0.5);
                subtitle.setAlpha(0);

                // fade in subtitle after title
                this.tweens.add({
                    targets: subtitle,
                    alpha: 1,
                    duration: 2000,
                    ease: 'Power1',
                    delay: 1000
                });

                const leaveText = this.add.text(400, 500, 'Press any key or click anywhere to exit...', {
                    fontFamily: 'Playfair Display',
                    fontSize: '20px',
                    color: '#999999',
                });
                leaveText.setOrigin(0.5);
                leaveText.setAlpha(0);

                // fade in the leave text last
                this.tweens.add({
                    targets: leaveText,
                    alpha: 1,
                    duration: 1000,
                    ease: 'Power1',
                    delay: 1500
                });

                // handle any keypress
                this.input.keyboard?.once('keydown', () => {
                    this.handleExit();
                });

                // handle any mouse/touch input
                this.input.once('pointerdown', () => {
                    this.handleExit();
                });
            }
        });
    }

    handleExit() {
        this.cameras.main.fade(1000, 0, 0, 0, false, (camera, progress) => {
            if (progress === 1) {
                // store door info before switching scenes
                const doorPosition = this.lastDoorPosition;

                // switch to town scene with data
                this.scene.start('TownScene', { fromInterior: true, doorPosition });
            }
        });
    }

    shutdown() {
        // clean up any ongoing tweens, timers, etc.
        this.tweens.killAll();
        this.time.removeAllEvents();
    }
}


const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 560;

const SCALE_FACTOR = Math.max(4, Math.round(window.innerWidth / CANVAS_WIDTH));  // note: prefer a round number here

/** @type {Phaser.Types.Core.GameConfig} */
const CONFIG = {
    type: Phaser.AUTO,                      // which renderer to use
    width: CANVAS_WIDTH,                    // canvas width in pixels
    height: CANVAS_HEIGHT,                  // canvas height in pixels
    parent: 'game-container',               // id of the dom element to add the canvas to
    scene: [TownScene, InteriorScene],
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { x: 0, y: 0 }         // top down game, so no gravity
        }
    },
    scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH,
        autoRound: true
    },
    render: {
        antialias: false,
        pixelArt: true,
        roundPixels: true,
        powerPreference: 'high-performance' // for better mobile performance
    }
};

const GAME = new Phaser.Game(CONFIG);
