import { AIAgent } from "./aiAgent";
import { PERSONALITY_BEHAVIORS } from "./personalities";
import { Character, ConversationStrategy, MessageAnalysis, PersonalityType, WORLD_SIZE } from "./types";
import { TFMessageAnalyzer } from './messageAnalysisTF';

export type ConversationStyle = 'basic' | 'emoji' | 'biased';

export interface ConversationSetupResult {
    characters: Map<string, Character>;
    strategy: BasicConversationStrategy | BiasedEmojiConversationStrategy | EmojiConversationStrategy;
}

export function setupConversationStyle(style: ConversationStyle, humanPlayerId: string): ConversationSetupResult {
    const newCharacters = new Map<string, Character>();

    // Add player
    newCharacters.set(humanPlayerId, {
        id: humanPlayerId,
        position: { x: 0, y: 0 },
        isHuman: true,
        name: 'Player'
    });

    const personalities: PersonalityType[] = [
        'shy', 'outgoing', 'formal', 'mysterious', 'playful', 'melancholic'
    ];

    if (style === 'biased') {
        const biasedStrategy = new BiasedEmojiConversationStrategy();

        personalities.forEach((personality, index) => {
            const id = `ai-${index}`;
            biasedStrategy.assignPersonality(id, personality);

            newCharacters.set(id, {
                id,
                position: {
                    x: Math.floor(Math.random() * WORLD_SIZE.x),
                    y: Math.floor(Math.random() * WORLD_SIZE.y)
                },
                isHuman: false,
                name: `${personality.charAt(0).toUpperCase() + personality.slice(1)} AI ${index + 1}`
            });
        });

        AIAgent.setConversationStrategy(biasedStrategy);
        return { characters: newCharacters, strategy: biasedStrategy };
    } else if (style === 'emoji') {
        // For emoji-based conversations with personalities
        const emojiStrategy = new EmojiConversationStrategy();

        personalities.forEach((personality, index) => {
            const id = `ai-${index}`;
            emojiStrategy.assignPersonality(id, personality);

            newCharacters.set(id, {
                id,
                position: {
                    x: Math.floor(Math.random() * WORLD_SIZE.x),
                    y: Math.floor(Math.random() * WORLD_SIZE.y)
                },
                isHuman: false,
                name: `${personality.charAt(0).toUpperCase() + personality.slice(1)} AI ${index + 1}`
            });
        });

        AIAgent.setConversationStrategy(emojiStrategy);
        return { characters: newCharacters, strategy: emojiStrategy };
    } else {
        // For basic text-based conversations
        const basicStrategy = new BasicConversationStrategy();
        AIAgent.setConversationStrategy(basicStrategy);

        // Add generic AI characters
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

        return { characters: newCharacters, strategy: basicStrategy };
    }
}

// Basic text-based conversation strategy
export class BasicConversationStrategy implements ConversationStrategy {
    private static readonly GREETINGS = [
        "Hello there! Would you like to chat?",
        "Hi human! How are you today?",
        "Hey! Nice to meet you!",
        "Lovely weather for a chat, isn't it?"
    ];

    private static readonly RESPONSES = [
        "That's interesting! Tell me more.",
        "I see what you mean. What made you think of that?",
        "How fascinating! And what do you think about...",
        "That reminds me of something similar...",
        "I've been wondering about that too!"
    ];

    getMovementModifiers(aiId: string) {
        return {
            moveChance: 0.3,    // Standard movement rate
            followChance: 0.3,  // Sometimes follows
            conversationChance: 0.1  // Occasionally starts conversations
        };
    }

    generateFirstMessage(): string {
        return BasicConversationStrategy.GREETINGS[
            Math.floor(Math.random() * BasicConversationStrategy.GREETINGS.length)
        ];
    }

    generateResponse(): string {
        return BasicConversationStrategy.RESPONSES[
            Math.floor(Math.random() * BasicConversationStrategy.RESPONSES.length)
        ];
    }
}

// Emoji-based conversation strategy with personalities

export class EmojiConversationStrategy implements ConversationStrategy {
    private personalities = new Map<string, PersonalityType>();

    getMovementModifiers(aiId: string) {
        const personality = this.getPersonality(aiId);
        const behavior = PERSONALITY_BEHAVIORS[personality];
        return {
            moveChance: behavior.moveChance,
            followChance: behavior.followChance,
            conversationChance: behavior.conversationChance
        };
    }

    assignPersonality(aiId: string, forcedType?: PersonalityType): PersonalityType {
        const type = forcedType || this.getRandomPersonality();
        this.personalities.set(aiId, type);
        return type;
    }

    getPersonality(aiId: string): PersonalityType {
        if (!this.personalities.has(aiId)) {
            this.assignPersonality(aiId);
        }
        return this.personalities.get(aiId)!;
    }

    private getRandomPersonality(): PersonalityType {
        const types = Object.keys(PERSONALITY_BEHAVIORS) as PersonalityType[];
        return types[Math.floor(Math.random() * types.length)];
    }

    generateFirstMessage(aiId: string): string {
        const personality = this.getPersonality(aiId);
        const behavior = PERSONALITY_BEHAVIORS[personality];
        const greetings = behavior.preferredEmojis.greeting;
        return greetings[Math.floor(Math.random() * greetings.length)];
    }

    generateResponse(message: string, aiId: string): string {
        const personality = this.getPersonality(aiId);
        const behavior = PERSONALITY_BEHAVIORS[personality];

        // Simple sentiment check
        const isPositive = message.match(/(love|happy|great|awesome|amazing|wonderful|good|nice|thank|please)/i);
        const isNegative = message.match(/(hate|sad|bad|awful|terrible|angry|upset|worried|scared)/i);

        // Simple intent check
        const isQuestion = message.endsWith('?');

        let emojiPool: string[] = [];

        if (isQuestion) {
            emojiPool.push(...behavior.preferredEmojis.question);
        } else {
            emojiPool.push(...behavior.preferredEmojis.statement);
        }

        if (isPositive) {
            emojiPool.push(...behavior.preferredEmojis.positive);
        } else if (isNegative) {
            emojiPool.push(...behavior.preferredEmojis.negative);
        } else {
            emojiPool.push(...behavior.preferredEmojis.neutral);
        }

        // Select 2-3 emojis
        const numEmojis = Math.floor(Math.random() * 2) + 2;
        const selectedEmojis = new Set<string>();

        while (selectedEmojis.size < numEmojis) {
            const randomEmoji = emojiPool[Math.floor(Math.random() * emojiPool.length)];
            selectedEmojis.add(randomEmoji);
        }

        return Array.from(selectedEmojis).join(' ');
    }
}

export class BiasedEmojiConversationStrategy implements ConversationStrategy {
    private personalities = new Map<string, PersonalityType>();

    constructor() {
        TFMessageAnalyzer.initialize().catch(error => {
            console.error('Failed to initialize message analyzer:', error);
        });
    }

    assignPersonality(aiId: string, forcedType?: PersonalityType): PersonalityType {
        const type = forcedType || this.getRandomPersonality();
        this.personalities.set(aiId, type);
        return type;
    }

    getPersonality(aiId: string): PersonalityType {
        if (!this.personalities.has(aiId)) {
            this.assignPersonality(aiId);
        }
        return this.personalities.get(aiId)!;
    }

    getMovementModifiers(aiId: string) {
        const personality = this.getPersonality(aiId);
        const behavior = PERSONALITY_BEHAVIORS[personality];
        return {
            moveChance: behavior.moveChance,
            followChance: behavior.followChance,
            conversationChance: behavior.conversationChance
        };
    }

    private getRandomPersonality(): PersonalityType {
        const types = Object.keys(PERSONALITY_BEHAVIORS) as PersonalityType[];
        return types[Math.floor(Math.random() * types.length)];
    }

    generateFirstMessage(aiId: string): string {
        const personality = this.getPersonality(aiId);
        const behavior = PERSONALITY_BEHAVIORS[personality];
        const greetings = behavior.preferredEmojis.greeting;
        return greetings[Math.floor(Math.random() * greetings.length)];
    }

    async generateResponse(message: string, aiId: string): Promise<string> {
        if (!TFMessageAnalyzer.isReady()) {
            console.warn('Message analyzer not ready, using basic response');
            return '💭 ✨';
        }

        try {
            const analysis = await TFMessageAnalyzer.analyzeMessage(message);
            return this.generateBiasedResponse(analysis, aiId);
        } catch (error) {
            console.error('Error generating response:', error);
            const personality = this.getPersonality(aiId);
            const behavior = PERSONALITY_BEHAVIORS[personality];
            return behavior.preferredEmojis.neutral[0] + ' ' + behavior.preferredEmojis.neutral[1];
        }
    }

    private generateBiasedResponse(analysis: MessageAnalysis, aiId: string): string {
        const personality = this.getPersonality(aiId);
        const behavior = PERSONALITY_BEHAVIORS[personality];

        // Apply personality bias to sentiment
        const adjustedSentiment = Math.max(-1, Math.min(1,
            analysis.sentiment + behavior.sentimentBias
        ));

        // Weight emotions based on personality
        const weightedEmotions = analysis.emotions
            .map(emotion => ({
                emotion,
                weight: behavior.emotionWeights[emotion] || 1.0
            }))
            .sort((a, b) => b.weight - a.weight);

        // Build emoji pool
        let emojiPool: string[] = [];

        // Add sentiment-based emojis
        if (adjustedSentiment > 0.3) {
            emojiPool.push(...behavior.preferredEmojis.positive);
        } else if (adjustedSentiment < -0.3) {
            emojiPool.push(...behavior.preferredEmojis.negative);
        } else {
            emojiPool.push(...behavior.preferredEmojis.neutral);
        }

        // Add intent-based emojis
        const intentEmojis = behavior.preferredEmojis[analysis.intent as keyof typeof behavior.preferredEmojis];
        if (intentEmojis) {
            emojiPool.push(...intentEmojis);
        }

        // Select final emojis with bias towards personality's preferred ones
        const selectedEmojis = new Set<string>();
        const numEmojis = analysis.confidence > behavior.confidenceThreshold ? 3 : 2;

        while (selectedEmojis.size < numEmojis) {
            const usePreferred = Math.random() < 0.7;
            const sourcePool = usePreferred ?
                behavior.preferredEmojis[adjustedSentiment > 0 ? 'positive' :
                                       adjustedSentiment < 0 ? 'negative' : 'neutral'] :
                emojiPool;

            const randomEmoji = sourcePool[Math.floor(Math.random() * sourcePool.length)];
            selectedEmojis.add(randomEmoji);
        }

        return Array.from(selectedEmojis).join(' ');
    }
}
