import { useEffect, useRef, useState } from 'react';
import { Character, Conversation, Message, HUMAN_PLAYER_ID, AI_RESPONSES } from '../types';

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
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        if (isInChatMode && inputRef.current) {
            inputRef.current.focus();
        }
    }, [activeConversation, isInChatMode]);

    if (!activeConversation) return null;

    const aiCharacter = selectedCharacter ? characters.get(selectedCharacter) : null;

    const handleSend = () => {
        if (!message.trim()) return;
        onSendMessage(message);
        setMessage('');
    };

    return (
        <div className={`p-4 border-l h-full max-h-[600px] overflow-hidden flex flex-col
            ${isInChatMode ? 'bg-white' : 'bg-gray-100'}`}>
            {aiCharacter && (
                <div className="text-lg font-bold mb-4 text-center">
                    Chatting with {aiCharacter.name}
                </div>
            )}

            <div className="h-full flex flex-col">
                <div className="flex-grow overflow-y-auto mb-4">
                    {activeConversation.messages.map((msg, i) => {
                        const author = characters.get(msg.authorId);
                        return (
                            <div key={i} className={`mb-2 p-2 rounded ${
                                msg.authorId === HUMAN_PLAYER_ID
                                    ? 'bg-blue-100 ml-4'
                                    : 'bg-gray-100 mr-4'
                            }`}>
                                <strong>{author?.name}:</strong> {msg.text}
                            </div>
                        );
                    })}
                    <div ref={messagesEndRef} />
                </div>

                <input
                    ref={inputRef}
                    type="text"
                    value={message}
                    onChange={e => setMessage(e.target.value)}
                    onKeyPress={e => e.key === 'Enter' && handleSend()}
                    className={`flex-grow px-2 py-1 border rounded
                        ${isInChatMode ? 'bg-white' : 'bg-gray-100'}`}
                    placeholder={isInChatMode ? "Type a message..." : "Press SPACE to chat"}
                    disabled={!isInChatMode}
                />
            </div>
        </div>
    );
}
