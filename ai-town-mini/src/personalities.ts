import { PersonalityBehavior, PersonalityType } from "./types";

export const PERSONALITY_BEHAVIORS: Record<PersonalityType, PersonalityBehavior> = {
    melancholic: {
        moveChance: 0.15,      // Moves slowly and reluctantly
        followChance: 0.05,    // Rarely follows others
        conversationChance: 0.07,  // Hesitant to start conversations
        sentimentBias: -0.3,   // Tends to see things more negatively
        confidenceThreshold: 0.4,  // Lower confidence in responses
        emotionWeights: {
            joy: 0.3,        // Rarely expresses joy
            sadness: 2.0,    // Often expresses sadness
            fear: 1.5,       // Often expresses anxiety
            surprise: 0.5,   // Rarely surprised
            neutral: 1.2     // Often neutral/resigned
        },
        preferredEmojis: {
            positive: ['⛅', '🌧️', '☔', '✨'],     // Even positive responses have rain
            negative: ['🌫️', '🍂', '🌧️', '☔'],    // Gloomy weather emojis
            neutral: ['🌫️', '☔', '...', '✨'],    // Misty, rainy
            greeting: ['🌧️ ☔', '🍂 🌫️ ...'],     // Subdued greetings
            question: ['☔', '🤔', '...'],         // Hesitant questions
            statement: ['🌫️', '🍂', '✨']          // Muted statements
        }
    },

    outgoing: {
        moveChance: 0.4,       // Very active
        followChance: 0.4,     // Often follows to interact
        conversationChance: 0.15,  // Eager to chat
        sentimentBias: 0.3,    // Sees things positively
        confidenceThreshold: 0.6,  // Confident in responses
        emotionWeights: {
            joy: 2.0,        // Very expressive of joy
            sadness: 0.3,    // Rarely shows sadness
            fear: 0.3,       // Rarely shows fear
            surprise: 1.5,   // Often excited/surprised
            neutral: 0.5     // Rarely neutral
        },
        preferredEmojis: {
            positive: ['🎉', '⭐', '💖', '✨'],     // Celebratory
            negative: ['💝', '✨', '💫', '🌟'],    // Still fairly positive
            neutral: ['⭐', '✨', '🌟'],           // Bright/sparkly
            greeting: ['🎉 💖 ✨', '⭐ 🌟 💖'],    // Enthusiastic greetings
            question: ['💫', '✨', '❓'],          // Excited questions
            statement: ['⭐', '💖', '✨']          // Energetic statements
        }
    },

    mysterious: {
        moveChance: 0.25,      // Moves unpredictably
        followChance: 0.15,    // Usually keeps distance
        conversationChance: 0.08,  // Selective about talking
        sentimentBias: 0.0,    // Neutral sentiment
        confidenceThreshold: 0.7,  // Only confident in specific situations
        emotionWeights: {
            joy: 0.8,        // Measured joy
            sadness: 0.8,    // Measured sadness
            fear: 1.2,       // Slight tendency toward mystical fear
            surprise: 1.5,   // Often enigmatically surprised
            neutral: 1.8     // Often mysteriously neutral
        },
        preferredEmojis: {
            positive: ['🔮', '✨', '🌌', '💫'],    // Mystical positivity
            negative: ['🌙', '💫', '🌌', '✨'],    // Mysterious negativity
            neutral: ['🔮', '💫', '🌌'],          // Enigmatic neutrality
            greeting: ['🔮 ✨', '🌌 💫'],         // Mysterious greetings
            question: ['🌌', '💫', '🔮'],         // Cryptic questions
            statement: ['✨', '🌙', '💫']         // Enigmatic statements
        }
    },

    formal: {
        moveChance: 0.3,       // Measured movements
        followChance: 0.2,     // Maintains professional distance
        conversationChance: 0.1,   // Professional approach to conversation
        sentimentBias: 0.1,    // Slightly positive/professional
        confidenceThreshold: 0.8,  // Very confident when speaking
        emotionWeights: {
            joy: 1.0,        // Measured joy
            sadness: 0.7,    // Restrained sadness
            fear: 0.7,       // Restrained fear
            surprise: 0.7,   // Restrained surprise
            neutral: 1.5     // Often professionally neutral
        },
        preferredEmojis: {
            positive: ['🤝', '✨', '📝', '💼'],    // Professional positivity
            negative: ['📝', '💼', '✒️', '💫'],    // Business-like negativity
            neutral: ['🎩', '✨', '💫'],          // Formal neutrality
            greeting: ['🤝 🎩', '💼 ✨'],         // Professional greetings
            question: ['📝', '✒️', '💫'],         // Formal questions
            statement: ['💼', '✨', '🎩']         // Professional statements
        }
    },

    shy: {
        moveChance: 0.2,       // Cautious movement
        followChance: 0.1,     // Prefers to keep distance
        conversationChance: 0.05,  // Hesitant to start conversations
        sentimentBias: -0.1,   // Slightly anxious sentiment
        confidenceThreshold: 0.5,  // Lower confidence threshold
        emotionWeights: {
            joy: 0.7,        // Quiet joy
            sadness: 1.2,    // More prone to sadness
            fear: 1.3,       // Often anxious
            surprise: 0.5,   // Easily startled
            neutral: 1.4     // Often quietly neutral
        },
        preferredEmojis: {
            positive: ['🌸', '✨', '💫', '🌱'],    // Gentle positivity
            negative: ['🍃', '🌱', '💫', '...'],   // Soft negativity
            neutral: ['✨', '🌸', '...', '💫'],    // Quiet neutrality
            greeting: ['🌸 ✨', '🌱 💫'],         // Gentle greetings
            question: ['💫', '...', '✨'],        // Hesitant questions
            statement: ['🌸', '🌱', '✨']         // Soft statements
        }
    },

    playful: {
        moveChance: 0.45,      // Very active movement
        followChance: 0.35,    // Likes to follow and play
        conversationChance: 0.12,  // Eager to interact playfully
        sentimentBias: 0.4,    // Very positive outlook
        confidenceThreshold: 0.5,  // Moderate confidence threshold
        emotionWeights: {
            joy: 2.0,        // Very joyful
            sadness: 0.2,    // Rarely sad
            fear: 0.3,       // Rarely afraid
            surprise: 1.8,   // Often playfully surprised
            neutral: 0.4     // Rarely neutral
        },
        preferredEmojis: {
            positive: ['🎈', '🎪', '🎮', '✨'],    // Fun and games
            negative: ['🎮', '🎯', '💫', '✨'],    // Still playful
            neutral: ['🎨', '✨', '🎈', '🎪'],     // Creative neutral
            greeting: ['🎈 ✨', '🎪 🎮'],         // Playful greetings
            question: ['🎮', '🎯', '✨'],         // Game-like questions
            statement: ['🎨', '🎈', '✨']         // Creative statements
        }
    }
};
