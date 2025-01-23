export type Position = { x: number; y: number };
export type Character = { id: string; position: Position; isHuman: boolean; name: string };
export type Message = { authorId: string; text: string; timestamp: number };
export type Conversation = { id: string; participants: string[]; messages: Message[] };

export const SPACE_CHAR = ' ';

export const WORLD_SIZE = { x: 12, y: 12 };
export const HUMAN_PLAYER_ID = 'human-1';
export const AI_GREETINGS = [
    "Hello there! Would you like to chat?",
    "Hi human! How are you today?",
    "Hey! Nice to meet you!",
    "Lovely weather for a chat, isn't it?"
];
export const AI_RESPONSES = [
    "That's interesting! Tell me more.",
    "I see what you mean. What made you think of that?",
    "How fascinating! And what do you think about...",
    "That reminds me of something similar...",
    "I've been wondering about that too!",
];
