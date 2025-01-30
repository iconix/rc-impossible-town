import { useEffect, useRef, useState } from 'react';
import { Character, Conversation, HUMAN_PLAYER_ID } from '../types';


interface Message {
    authorId: string;
    text: string | Promise<string>;
    timestamp: number;
  }

  interface ResolvedMessage {
    authorId: string;
    text: string;
    timestamp: number;
  }

interface ChatBoxProps {
    characters: Map<string, Character>;
    activeConversation: Conversation | null;
    selectedCharacter: string | null;
    isInChatMode: boolean;
    onSendMessage: (text: string) => void;
    inputRef: React.RefObject<HTMLInputElement>;
}

export function ChatBox({
    characters,
    activeConversation,
    selectedCharacter,
    isInChatMode,
    onSendMessage,
    inputRef
}: ChatBoxProps) {
    const [message, setMessage] = useState('');
    const [resolvedMessages, setResolvedMessages] = useState<ResolvedMessage[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [resolvedMessages]);

    // Focus input when entering chat mode
    useEffect(() => {
        if (isInChatMode && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isInChatMode, inputRef]);

    // Effect to resolve any Promise messages
    useEffect(() => {
        if (!activeConversation) return;

        const resolveMessages = async () => {
            const newMessages = await Promise.all(
                activeConversation.messages.map(async (msg) => ({
                    authorId: msg.authorId,
                    text: typeof msg.text === 'string' ? msg.text : await msg.text,
                    timestamp: msg.timestamp
                }))
            );
            setResolvedMessages(newMessages);
        };

        resolveMessages();
    }, [activeConversation]);

    const handleSendMessage = () => {
        if (!message.trim()) return;
        onSendMessage(message);
        setMessage('');
    };

    const aiCharacterName = selectedCharacter ? characters.get(selectedCharacter)?.name : null;

    if (!activeConversation) return null;

    return (
        <div className={`p-4 border-l h-full max-h-[600px] overflow-hidden flex flex-col
            ${isInChatMode ? 'bg-white' : 'bg-gray-100'}`}>
            {aiCharacterName && (
                <div className="text-lg font-bold mb-4 text-center">
                    Chatting with {aiCharacterName}
                </div>
            )}

            <div className="h-full flex flex-col">
                <div className="flex-grow overflow-y-auto mb-4">
                    {resolvedMessages.map((msg, i) => {
                        const author = characters.get(msg.authorId);
                        return (
                            <div key={i} className={`mb-2 p-2 rounded ${
                                msg.authorId === 'human-1'
                                    ? 'bg-blue-100 ml-4'
                                    : 'bg-gray-100 mr-4'
                            }`}>
                                <strong>{author?.name}:</strong> {msg.text}
                            </div>
                        );
                    })}
                    <div ref={messagesEndRef} />
                </div>

                <div className="mt-auto flex gap-2">
                    <input
                        ref={inputRef}
                        type="text"
                        value={message}
                        onChange={e => setMessage(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                        className={`flex-grow px-2 py-1 border rounded
                            ${isInChatMode ? 'bg-white' : 'bg-gray-100'}`}
                        placeholder={isInChatMode ? "Type a message..." : "Press SPACE to chat"}
                        disabled={!isInChatMode}
                    />
                </div>
            </div>
        </div>
    );
}
