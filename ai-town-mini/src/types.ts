export type Position = { x: number; y: number };
export type Character = { id: string; position: Position; isHuman: boolean; name: string };
export type Message = { authorId: string; text: string | Promise<string>; timestamp: number };
export type Conversation = { id: string; participants: string[]; messages: Message[] };

export const SPACE_CHAR = ' ';

export const WORLD_SIZE = { x: 12, y: 12 };
export const HUMAN_PLAYER_ID = 'human-1';

export type PersonalityType = 'shy' | 'outgoing' | 'formal' | 'mysterious' | 'playful' | 'melancholic';

export interface PersonalityBehavior {
    // Movement patterns
    moveChance: number;
    followChance: number;
    conversationChance: number;

    // Message analysis adjustments
    sentimentBias: number;
    emotionWeights: Record<string, number>;
    confidenceThreshold: number;

    // Response style
    preferredEmojis: {
        positive: string[];
        negative: string[];
        neutral: string[];
        greeting: string[];
        question: string[];
        statement: string[];
    };
}

export interface MessageAnalysis {
    sentiment: number;  // -1 to 1
    emotions: string[];
    intent: string;
    confidence: number;
}

export interface ConversationStrategy {
    generateFirstMessage(aiId: string): string | Promise<string>;
    generateResponse(message: string, aiId: string): string | Promise<string>;
    getMovementModifiers(aiId: string): {
        moveChance: number;
        followChance: number;
        conversationChance: number;
    };
}
