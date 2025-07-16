import { useRef, useState } from 'react';

import { ChatContent } from '@/api/chat';
import { createChatStream } from '@/api/chat';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: ChatContent;
}

// import { v4 as uuidv4 } from 'uuid';
// import {
//   ChatHistoryItem,
//   getChatHistory,
//   saveChatToLocal,
// } from '@/utils/chatStorage';
// import { ChatContent } from '@/api/chat';
// import { ChatMessage, ChatResponse, sendChatMessage } from '@/api/chat';

export const useChat = () => {
  // const [messages, setMessages] = useState<ChatMessage[]>([]);
  // const [input, setInput] = useState('');
  // const [isStreaming, setIsStreaming] = useState(false);
  //   const [typingText, setTypingText] = useState('');
  //   const [chatHistory, setChatHistory] = useState<ChatHistoryItem[]>([]);
  //   const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  //   const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);
  //   const [completeResponse, setCompleteResponse] = useState<ChatContent[]>([]);
  //   const typingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  //   const selectChat = (chatId: string, messages: ChatMessage[]) => {
  //     setCurrentChatId(chatId);
  //     setMessages(messages);
  //     setIsStreaming(false);
  //     setTypingText('');
  //     setCompleteResponse([]);
  //     setLastResponse(null);
  //   };

  //   const startNewChat = () => {
  //     const newChatId = uuidv4();
  //     setCurrentChatId(newChatId);
  //     setMessages([]);
  //     setTypingText('');
  //     setInput('');
  //   };

  //   const sendMessage = async () => {
  //     if (!input.trim() || !currentChatId) return;

  //     const userMessage = { role: 'user', content: input };
  //     const updatedMessages = [...messages, userMessage];
  //     setMessages(updatedMessages);
  //     setInput('');
  //     setIsStreaming(true);
  //     setTypingText('');
  //     setCompleteResponse([]);
  //     // setLastResponse(null);

  //     if (chatHistory.every((chat) => chat.id !== currentChatId)) {
  //       const newChat = {
  //         id: currentChatId,
  //         title: '',
  //         messages: updatedMessages,
  //         createdAt: new Date().toISOString(),
  //       };
  //       const updatedHistory = [newChat, ...chatHistory];
  //       localStorage.setItem('chatHistory', JSON.stringify(updatedHistory));
  //       setChatHistory(updatedHistory);
  //     }

  //     setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

  //     try {
  //       const response = await sendChatMessage({
  //         uuid: 'test',
  //         question: input,
  //         messages: updatedMessages.slice(0, -1),
  //       });

  //       setLastResponse((prev) => {
  //         if (prev !== null) {
  //           return {
  //             ...response,
  //             title: prev.title,
  //           };
  //         }

  //         return response;
  //       });

  //       setCompleteResponse(response.answer);

  //       let index = 0;
  //       const fullText = response.answer.map((a) => a.paragraph).join('\n\n');

  //       typingIntervalRef.current = setInterval(() => {
  //         setTypingText(fullText.slice(0, ++index));
  //         if (index >= fullText.length) {
  //           clearInterval(typingIntervalRef.current!);
  //           typingIntervalRef.current = null;
  //           setIsStreaming(false);
  //         }
  //       }, 10);
  //     } catch (error) {
  //       console.error('챗봇 응답 실패:', error);
  //       setIsStreaming(false);

  //       setMessages((prev) => {
  //         const updated = [...prev];
  //         updated[updated.length - 1] = {
  //           role: 'assistant',
  //           content: '답변 생성 중 오류가 발생하였습니다.',
  //         };
  //         return updated;
  //       });
  //     }
  //   };

  //   const cancelStreamingResponse = () => {
  //     if (typingIntervalRef.current) {
  //       clearInterval(typingIntervalRef.current);
  //       typingIntervalRef.current = null;
  //     }

  //     setIsStreaming(false);

  //     setMessages((prev) => {
  //       const updated = [...prev];
  //       const completedBotMessage = {
  //         role: 'assistant' as const,
  //         content: completeResponse,
  //       };
  //       updated[updated.length - 1] = completedBotMessage;
  //       return updated;
  //     });
  //   };

  //   useEffect(() => {
  //     if (!isStreaming && typingText && currentChatId) {
  //       setMessages((prev) => {
  //         const updatedMessages = [...prev];

  //         const lastBotMessage = {
  //           role: 'assistant' as const,
  //           content: completeResponse,
  //         };

  //         updatedMessages[updatedMessages.length - 1] = lastBotMessage;
  //         const title = lastResponse?.title || '새로운 대화';

  //         saveChatToLocal(currentChatId, { title, messages: updatedMessages });
  //         setChatHistory(getChatHistory());

  //         return updatedMessages;
  //       });
  //     }
  //   }, [isStreaming, typingText, completeResponse, lastResponse, currentChatId]);

  // TODO: new
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<(() => void) | null>(null);

  const sendMessage = (input: string) => {
    const newMessage: ChatMessage = {
      role: 'user',
      content: { message: input },
    };

    setMessages((prev) => [...prev, newMessage]);
    setIsStreaming(true);

    abortRef.current = createChatStream({ message: input }, (data) => {
      if (data.status === 'pending' && data.content?.message) {
        setPendingMessage(data.content.message);
      }

      if (data.status === 'response') {
        setPendingMessage(null);

        setMessages((prev) => {
          const last = prev.at(-1);
          const isLastAssistant = last?.role === 'assistant';

          if (data.content?.products && !data.content?.message) {
            return [
              ...prev,
              {
                role: 'assistant',
                content: { products: data.content.products },
              },
            ];
          }

          if (data.content?.message) {
            if (isLastAssistant && last?.content.message !== undefined) {
              return [
                ...prev.slice(0, -1),
                {
                  role: 'assistant',
                  content: {
                    ...last.content,
                    message:
                      (last.content.message || '') + data.content.message,
                  },
                },
              ];
            }

            return [
              ...prev,
              { role: 'assistant', content: { message: data.content.message } },
            ];
          }

          return prev;
        });
      }

      if (data.status === 'stop') {
        setPendingMessage(null);
        setIsStreaming(false);
      }
    });
  };

  const cancelStreamingResponse = () => {
    if (abortRef.current) {
      abortRef.current(); // AbortController.abort()
      setIsStreaming(false);
    }
  };

  return {
    messages,
    pendingMessage,
    isStreaming,
    input,
    setInput,
    sendMessage,
    cancelStreamingResponse,
  };
};
