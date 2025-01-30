import { BasicConversationStrategy, EmojiConversationStrategy } from './conversationStrategies';
import { Character, Position, HUMAN_PLAYER_ID, Conversation, WORLD_SIZE, ConversationStrategy } from './types';



interface AIContext {
    characters: Map<string, Character>;
    conversations: Map<string, Conversation>;
    isInChatMode: boolean;
    hasActiveConversation: boolean;
}

interface AIAction {
    type: 'move' | 'initiate_conversation' | 'respond';
    aiId: string;
    data?: {
        position?: Position;
        message?: string;
        conversationId?: string;
    };
}

export class AIAgent {
    private static conversationStrategy: ConversationStrategy = new BasicConversationStrategy();

    static setConversationStrategy(strategy: ConversationStrategy) {
        this.conversationStrategy = strategy;
    }

    static getConversationStrategy(): ConversationStrategy {
        return this.conversationStrategy;
    }

    static updateAIs(context: AIContext): AIAction[] {
        const actions: AIAction[] = [];
        const player = context.characters.get(HUMAN_PLAYER_ID);
        if (!player) return actions;

        // Get movement modifiers if using EmojiConversationStrategy
        const getModifiers = (aiId: string) => {
            if (this.conversationStrategy instanceof EmojiConversationStrategy) {
                return this.conversationStrategy.getMovementModifiers(aiId);
            }
            return {
                moveChance: 0.3,
                followChance: 0.3,
                conversationChance: 0.1
            };
        };

        // Only consider conversations where chat mode is active
        const anyAIInConversation = Array.from(context.conversations.values())
            .some(conv =>
                conv.participants.includes(HUMAN_PLAYER_ID) &&
                conv.messages.length > 0 &&
                context.isInChatMode
            );

        context.characters.forEach((char, id) => {
            if (char.isHuman) return;

            const modifiers = getModifiers(id);

            // Check if this specific AI is in an active conversation
            const isInConversation = Array.from(context.conversations.values())
                .some(conv =>
                    conv.participants.includes(id) &&
                    conv.participants.includes(HUMAN_PLAYER_ID) &&
                    conv.messages.length > 0 &&
                    context.isInChatMode
                );

            // If this AI is in an active conversation, don't move at all
            if (isInConversation) return;

            // If another AI is in an active conversation, only do random movements
            if (anyAIInConversation) {
                if (Math.random() < modifiers.moveChance) {
                    const newPosition = this.calculateRandomPosition(char);
                    if (this.isValidPosition(newPosition, context)) {
                        actions.push({
                            type: 'move',
                            aiId: id,
                            data: { position: newPosition }
                        });
                    }
                }
                return;
            }

            // Otherwise, no conversations are happening
            if (Math.random() < modifiers.moveChance) {
                let newPosition;
                if (Math.random() < modifiers.followChance) {
                    // Move towards player based on personality
                    newPosition = this.calculateFollowPosition(char, player);
                } else {
                    // Random movement
                    newPosition = this.calculateRandomPosition(char);
                }

                if (this.isValidPosition(newPosition, context)) {
                    actions.push({
                        type: 'move',
                        aiId: id,
                        data: { position: newPosition }
                    });
                }
            }

            // Check for conversation initiation
            const isAdjacent = this.isAdjacentToPlayer(char, player);
            if (isAdjacent && !context.hasActiveConversation &&
                Math.random() < modifiers.conversationChance) {
                actions.push({
                    type: 'initiate_conversation',
                    aiId: id
                });
            }
        });

        return actions;
    }

    static generateFirstMessage(aiId: string): string | Promise<string> {
        return this.conversationStrategy.generateFirstMessage(aiId);
    }

    static generateResponse(message: string, aiId: string): string | Promise<string> {
        return this.conversationStrategy.generateResponse(message, aiId);
    }

    private static isAdjacentToPlayer(ai: Character, player: Character): boolean {
        const dx = Math.abs(player.position.x - ai.position.x);
        const dy = Math.abs(player.position.y - ai.position.y);
        // Only allow cardinal directions (up, down, left, right)
        return (dx === 1 && dy === 0) || (dx === 0 && dy === 1);
    }

    private static calculateRandomPosition(char: Character): Position {
        const newPosition = { ...char.position };
        const direction = Math.floor(Math.random() * 4);
        switch (direction) {
            case 0: newPosition.y--; break; // up
            case 1: newPosition.y++; break; // down
            case 2: newPosition.x--; break; // left
            case 3: newPosition.x++; break; // right
        }
        return newPosition;
    }

    private static calculateFollowPosition(char: Character, player: Character): Position {
        const newPosition = { ...char.position };
        if (player.position.x > char.position.x) newPosition.x++;
        else if (player.position.x < char.position.x) newPosition.x--;
        if (player.position.y > char.position.y) newPosition.y++;
        else if (player.position.y < char.position.y) newPosition.y--;
        return newPosition;
    }

    private static isValidPosition(position: Position, context: AIContext): boolean {
        // Check world bounds
        if (position.x < 0 || position.x >= WORLD_SIZE.x ||
            position.y < 0 || position.y >= WORLD_SIZE.y) {
            return false;
        }

        // Check collisions with other characters
        for (const char of context.characters.values()) {
            if (char.position.x === position.x && char.position.y === position.y) {
                return false;
            }
        }

        return true;
    }
}
