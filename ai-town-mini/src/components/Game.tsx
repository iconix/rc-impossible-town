import { useCallback, useEffect, useRef, useState } from 'react';
import { ChatBox } from './ChatBox';
import { Grid } from './Grid';
import { Position, Character, Conversation, WORLD_SIZE, HUMAN_PLAYER_ID, AI_RESPONSES, AI_GREETINGS, SPACE_CHAR } from '../types';
import { AIAgent } from '../aiAgent';

export default function Game() {
    // Game state
    const [characters, setCharacters] = useState<Map<string, Character>>(new Map());
    const [conversations, setConversations] = useState<Map<string, Conversation>>(new Map());
    const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
    const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
    const [isInChatMode, setIsInChatMode] = useState(false);
    const chatInputRef = useRef<HTMLInputElement>(null);

    // Initialize game
    useEffect(() => {
        const newCharacters = new Map<string, Character>();

        // Add player
        newCharacters.set(HUMAN_PLAYER_ID, {
            id: HUMAN_PLAYER_ID,
            position: { x: 0, y: 0 },
            isHuman: true,
            name: 'Player'
        });

        // Add AI characters
        for (let i = 0; i < 5; i++) {
            const id = `ai-${i}`;
            newCharacters.set(id, {
                id,
                position: {
                    x: Math.floor(Math.random() * WORLD_SIZE.x),
                    y: Math.floor(Math.random() * WORLD_SIZE.y)
                },
                isHuman: false,
                name: `AI ${i + 1}`
            });
        }

        setCharacters(newCharacters);
    }, []);

    const moveCharacter = useCallback((characterId: string, newPos: Position): boolean => {
        const character = characters.get(characterId);
        if (!character) return false;

        // Check bounds and collisions
        if (newPos.x < 0 || newPos.x >= WORLD_SIZE.x ||
            newPos.y < 0 || newPos.y >= WORLD_SIZE.y) return false;

        // Check if position is occupied
        for (const char of characters.values()) {
            if (char.position.x === newPos.x && char.position.y === newPos.y) {
                return false;
            }
        }

        // Update position
        setCharacters(chars => {
            const newChars = new Map(chars);
            newChars.set(characterId, { ...character, position: newPos });
            return newChars;
        });

        return true;
    }, [characters]);

    const findOrStartConversation = useCallback((aiId: string, shouldGreet = false) => {
        // Try to find an existing conversation
        const existingConversation = Array.from(conversations.values()).find(conv =>
            conv.participants.includes(HUMAN_PLAYER_ID) &&
            conv.participants.includes(aiId)
        );

        if (existingConversation) {
            // If we found an existing conversation and need to greet,
            // add greeting to the existing conversation
            if (shouldGreet) {
                const greeting = AI_GREETINGS[Math.floor(Math.random() * AI_GREETINGS.length)];
                const updatedConversation = {
                    ...existingConversation,
                    messages: [...existingConversation.messages, {
                        authorId: aiId,
                        text: greeting,
                        timestamp: Date.now()
                    }]
                };
                setConversations(convs => {
                    const newConvs = new Map(convs);
                    newConvs.set(existingConversation.id, updatedConversation);
                    return newConvs;
                });
                setActiveConversation(updatedConversation);
            } else {
                setActiveConversation(existingConversation);
            }
            return existingConversation.id;
        }

        // If no existing conversation, create a new one
        const conversationId = crypto.randomUUID();
        const newConversation: Conversation = {
            id: conversationId,
            participants: [HUMAN_PLAYER_ID, aiId],
            messages: shouldGreet ? [{
                authorId: aiId,
                text: AI_GREETINGS[Math.floor(Math.random() * AI_GREETINGS.length)],
                timestamp: Date.now()
            }] : []
        };


        setConversations(convs => {
            const newConvs = new Map(convs);
            newConvs.set(conversationId, newConversation);
            return newConvs;
        });

        setActiveConversation(newConversation);
        return conversationId;
    }, [conversations]);

    const handleSendMessage = useCallback((text: string) => {
        if (!activeConversation) return;

        const updatedConversation = {
            ...activeConversation,
            messages: [
                ...activeConversation.messages,
                { authorId: HUMAN_PLAYER_ID, text, timestamp: Date.now() }
            ]
        };

        setConversations(convs => {
            const newConvs = new Map(convs);
            newConvs.set(activeConversation.id, updatedConversation);
            return newConvs;
        });
        setActiveConversation(updatedConversation);

        // AI response
        setTimeout(() => {
            const aiResponse = AI_RESPONSES[Math.floor(Math.random() * AI_RESPONSES.length)];
            const aiParticipant = activeConversation.participants.find(id => id !== HUMAN_PLAYER_ID);

            if (aiParticipant) {
                const conversationWithResponse = {
                    ...updatedConversation,
                    messages: [
                        ...updatedConversation.messages,
                        { authorId: aiParticipant, text: aiResponse, timestamp: Date.now() }
                    ]
                };

                setConversations(convs => {
                    const newConvs = new Map(convs);
                    newConvs.set(activeConversation.id, conversationWithResponse);
                    return newConvs;
                });
                setActiveConversation(conversationWithResponse);
            }
        }, 1000);
    }, [activeConversation]);

    useEffect(() => {
        const handleKeyPress = (e: KeyboardEvent) => {
            const player = characters.get(HUMAN_PLAYER_ID);
            if (!player) return;

            if (e.key === 'Escape' && isInChatMode) {
                setIsInChatMode(false);
                setSelectedCharacter(null);
                setActiveConversation(null);
                chatInputRef.current?.blur();
                return;
            }

            if (e.key === SPACE_CHAR && !isInChatMode) {
                e.preventDefault();
                const player = characters.get(HUMAN_PLAYER_ID);
                if (!player) return;

                // Find adjacent AI
                for (const [id, char] of characters.entries()) {
                    if (!char.isHuman) {
                        const dx = Math.abs(player.position.x - char.position.x);
                        const dy = Math.abs(player.position.y - char.position.y);
                        // Only allow cardinal directions (up, down, left, right)
                        if ((dx === 1 && dy === 0) || (dx === 0 && dy === 1)) {
                            setIsInChatMode(true);
                            setSelectedCharacter(id);
                            findOrStartConversation(id, false);  // Player initiating, no greeting needed
                            chatInputRef.current?.focus();
                            break;
                        }
                    }
                }
                return;
            }

            if (!isInChatMode) {
                const movements = {
                    ArrowUp: { ...player.position, y: player.position.y - 1 },
                    ArrowDown: { ...player.position, y: player.position.y + 1 },
                    ArrowLeft: { ...player.position, x: player.position.x - 1 },
                    ArrowRight: { ...player.position, x: player.position.x + 1 }
                };

                if (e.key in movements) {
                    moveCharacter(HUMAN_PLAYER_ID, movements[e.key as keyof typeof movements]);
                }
            }
        };

        window.addEventListener('keydown', handleKeyPress);
        return () => window.removeEventListener('keydown', handleKeyPress);
    }, [characters, isInChatMode, moveCharacter, findOrStartConversation]);

    // AI update loop
    useEffect(() => {
        const updateAIs = () => {
            const aiContext = {
                characters,
                conversations,
                isInChatMode,
                hasActiveConversation: activeConversation !== null
            };

            const actions = AIAgent.updateAIs(aiContext);

            // Process AI actions
            actions.forEach(action => {
                switch (action.type) {
                    case 'move':
                        if (action.data?.position) {
                            moveCharacter(action.aiId, action.data.position);
                        }
                        break;

                    case 'initiate_conversation':
                        setIsInChatMode(true);
                        setSelectedCharacter(action.aiId);
                        findOrStartConversation(action.aiId, true);
                        break;
                }
            });
        };

        // Update AIs every 1 second
        const interval = setInterval(updateAIs, 1000);
        return () => clearInterval(interval);
    }, [characters, isInChatMode, activeConversation, moveCharacter, findOrStartConversation]);

    return (
        <div className="flex flex-col items-center">
            <div className="p-4 text-center text-gray-600 mb-4">
                <div>Use arrow keys to move your character</div>
                <div className="text-sm mt-1 text-gray-500">
                    Press SPACE to chat when next to another character, ESC to exit chat
                </div>
            </div>
            <div className="flex justify-center w-full max-w-4xl mx-auto px-4">
                <div className={`flex-1 flex justify-center ${isInChatMode ? 'opacity-50' : ''}`}>
                    <Grid
                        characters={Array.from(characters.values())}
                        selectedCharacter={selectedCharacter}
                        onTileClick={(x, y) => {
                            if (selectedCharacter) {
                                moveCharacter(selectedCharacter, { x, y });
                            }
                        }}
                        onCharacterClick={id => {
                            if (id === HUMAN_PLAYER_ID) return;
                            setIsInChatMode(false);
                            setSelectedCharacter(id);
                            setActiveConversation(null);
                        }}
                        isInChatMode={isInChatMode}
                        activeConversation={activeConversation}
                    />
                </div>
                <div className="w-[300px] ml-8">
                    <ChatBox
                        characters={characters}
                        activeConversation={activeConversation}
                        selectedCharacter={selectedCharacter}
                        isInChatMode={isInChatMode}
                        onSendMessage={handleSendMessage}
                        inputRef={chatInputRef}
                    />
                </div>
            </div>
        </div>
    );
}
