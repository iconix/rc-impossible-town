import * as tf from '@tensorflow/tfjs';
import * as use from '@tensorflow-models/universal-sentence-encoder';
import { MessageAnalysis } from './types';

export class TFMessageAnalyzer {
    private static encoder: use.UniversalSentenceEncoder | null = null;
    private static isInitialized = false;

    // Reference sentences for sentiment comparison
    private static readonly SENTIMENT_REFERENCES = {
        positive: [
            "I love this",
            "This is wonderful",
            "I'm happy",
            "Great job",
            "This is amazing",
            "Excellent work",
            "I'm excited",
            "Perfect solution",
            "Very helpful",
            "Thank you so much"
        ],
        negative: [
            "I hate this",
            "This is terrible",
            "I'm sad",
            "Poor job",
            "This is awful",
            "Disappointing result",
            "I'm frustrated",
            "Bad solution",
            "Not helpful at all",
            "This is a waste"
        ]
    };

    // Reference sentences for intent classification
    private static readonly INTENT_REFERENCES = {
        greeting: [
            "hello there",
            "hi how are you",
            "good morning",
            "hey friend",
            "greetings"
        ],
        question: [
            "what is this",
            "how does this work",
            "where can i find",
            "when will it be ready",
            "who is responsible"
        ],
        farewell: [
            "goodbye for now",
            "see you later",
            "have a good day",
            "bye bye",
            "farewell friend"
        ],
        statement: [
            "i think that",
            "in my opinion",
            "let me tell you",
            "i believe",
            "the fact is"
        ]
    };

    private static positiveEmbedding: tf.Tensor | null = null;
    private static negativeEmbedding: tf.Tensor | null = null;
    private static intentEmbeddings: Record<string, tf.Tensor> = {};

    static async initialize(): Promise<void> {
        if (this.isInitialized) return;

        try {
            console.log('Loading Universal Sentence Encoder...');
            this.encoder = await use.load();

            // Pre-compute sentiment embeddings
            // Cast the embeddings to Tensor2D (adding 'unknown' conversion for non-overlapping types)
            this.positiveEmbedding = (await this.encoder.embed(this.SENTIMENT_REFERENCES.positive)) as unknown as tf.Tensor2D;
            this.negativeEmbedding = (await this.encoder.embed(this.SENTIMENT_REFERENCES.negative)) as unknown as tf.Tensor2D;

            // Pre-compute intent embeddings
            // Cast the embeddings to Tensor2D (adding 'unknown' conversion for non-overlapping types)
            for (const [intent, examples] of Object.entries(this.INTENT_REFERENCES)) {
                this.intentEmbeddings[intent] = (await this.encoder.embed(examples)) as unknown as tf.Tensor2D;
            }

            this.isInitialized = true;
            console.log('Message analyzer initialized successfully');
        } catch (error) {
            console.error('Failed to initialize message analyzer:', error);
            throw error;
        }
    }

    static async analyzeMessage(message: string): Promise<MessageAnalysis> {
        if (!this.isInitialized || !this.encoder) {
            throw new Error('Message analyzer not initialized');
        }

        // Cast the embeddings to Tensor2D (adding 'unknown' conversion for non-overlapping types)
        const messageEmbedding = (await this.encoder.embed([message])) as unknown as tf.Tensor2D;

        // Calculate sentiment using cosine similarity
        const positiveSimilarity = tf.tidy(() => {
            const similarity = this.calculateCosineSimilarity(messageEmbedding, this.positiveEmbedding!);
            return similarity.max().dataSync()[0];
        });

        const negativeSimilarity = tf.tidy(() => {
            const similarity = this.calculateCosineSimilarity(messageEmbedding, this.negativeEmbedding!);
            return similarity.max().dataSync()[0];
        });

        // Calculate sentiment score (-1 to 1)
        const sentiment = (positiveSimilarity - negativeSimilarity);

        // Determine intent
        const { intent, confidence } = await this.classifyIntent(messageEmbedding, message);

        // Detect emotions based on sentiment and patterns
        const emotions = this.detectEmotions(message, sentiment);

        messageEmbedding.dispose();

        return {
            sentiment,
            emotions,
            intent,
            confidence
        };
    }

    private static calculateCosineSimilarity(a: tf.Tensor, b: tf.Tensor): tf.Tensor {
        return tf.tidy(() => {
            const normalizedA = tf.div(a, tf.norm(a));
            const normalizedB = tf.div(b, tf.norm(b));
            return tf.matMul(normalizedA, normalizedB, false, true);
        });
    }

    private static async classifyIntent(messageEmbedding: tf.Tensor, message: string): Promise<{ intent: string, confidence: number }> {
        let highestSimilarity = -1;
        let bestIntent = 'statement';

        for (const [intent, embedding] of Object.entries(this.intentEmbeddings)) {
            const similarity = tf.tidy(() => {
                const cosineSimilarity = this.calculateCosineSimilarity(messageEmbedding, embedding);
                return cosineSimilarity.max().dataSync()[0];
            });

            if (similarity > highestSimilarity) {
                highestSimilarity = similarity;
                bestIntent = intent;
            }
        }

        // Special case for questions (high confidence if question mark present)
        if (bestIntent === 'question' || message.endsWith('?')) {
            return { intent: 'question', confidence: 0.95 };
        }

        return {
            intent: bestIntent,
            confidence: Math.max(0.6, highestSimilarity) // Minimum confidence of 0.6
        };
    }

    private static detectEmotions(message: string, sentiment: number): string[] {
        const emotions = new Set<string>();
        const lowerMessage = message.toLowerCase();

        // Emotion detection based on both keyword matching and sentiment
        if (sentiment > 0.5 || lowerMessage.match(/(happy|joy|great|wonderful|love)/)) {
            emotions.add('joy');
        }
        if (sentiment < -0.5 || lowerMessage.match(/(sad|unhappy|disappointed|sorry)/)) {
            emotions.add('sadness');
        }
        if (lowerMessage.match(/(wow|whoa|amazing|incredible)/)) {
            emotions.add('surprise');
        }
        if (lowerMessage.match(/(afraid|scared|worried|nervous)/)) {
            emotions.add('fear');
        }

        if (emotions.size === 0) {
            emotions.add(sentiment > 0 ? 'joy' : sentiment < 0 ? 'sadness' : 'neutral');
        }

        return Array.from(emotions);
    }

    static isReady(): boolean {
        return this.isInitialized;
    }
}
