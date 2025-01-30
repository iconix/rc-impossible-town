import { Character, Conversation, WORLD_SIZE } from '../types';

interface GridProps {
    characters: Character[];
    selectedCharacter: string | null;
    onTileClick: (x: number, y: number) => void;
    onCharacterClick: (id: string) => void;
    isInChatMode: boolean;
    activeConversation: Conversation | null;
}

export function Grid({
    characters,
    selectedCharacter,
    onTileClick,
    onCharacterClick,
    isInChatMode,
    activeConversation
}: GridProps) {
    const findFirstCharacterOrWithNumber = (str: string) => (str.match(/\d+/) ? str.charAt(0) + str.match(/\d+/)[0] : str.charAt(0));

    const isCharacterTalking = (character: Character) => {
        return isInChatMode &&
               activeConversation?.participants.includes(character.id);
    };

    return (
        <div
            className="grid gap-0"
            style={{ gridTemplateColumns: `repeat(${WORLD_SIZE.x}, 30px)` }}
        >
            {Array.from({ length: WORLD_SIZE.y }, (_, y) =>
                Array.from({ length: WORLD_SIZE.x }, (_, x) => {
                    const character = characters.find(
                        char => char.position.x === x && char.position.y === y
                    );

                    return (
                        <div
                            key={`${x}-${y}`}
                            className={`
                                w-[30px] h-[30px] border border-gray-200
                                hover:bg-gray-100
                                ${character ? 'cursor-pointer' : 'cursor-default'}
                                ${character?.id === selectedCharacter ? 'bg-blue-200' : 'bg-white'}
                            `}
                            onClick={() => character ? onCharacterClick(character.id) : onTileClick(x, y)}
                        >
                            {character && (
                                <div className={`
                                    w-full h-full relative
                                    flex items-center justify-center
                                    ${character.isHuman ? 'bg-green-500' : 'bg-red-500'}
                                    text-white text-xs font-bold rounded-full
                                    transition-all duration-200
                                    ${isCharacterTalking(character) ? 'ring-2 ring-yellow-300 ring-offset-1' : ''}
                                `}>
                                    {findFirstCharacterOrWithNumber(character.name)}
                                    {isCharacterTalking(character) && !character.isHuman && (
                                        <div className="absolute -top-2 -right-2 text-yellow-300 animate-bounce">
                                            💭
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    );
                })
            )}
        </div>
    );
}
