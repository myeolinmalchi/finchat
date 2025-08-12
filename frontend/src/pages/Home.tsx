import { useEffect, useRef } from 'react';

import { useParams } from 'react-router-dom';

import { useChatListStore } from '@/stores/chatListStore';

import { getChatDetail } from '@/api/chat';

import { useChat } from '@/hooks/useChat';
import { useChatList } from '@/hooks/useChatList';

import { ChatInput } from '@/components/ChatInput';
import { MessageItem } from '@/components/MessageItem';
import { Sidebar } from '@/components/Sidebar';

export const HomePage = () => {
  const { data: chatListData } = useChatList();
  const setChatList = useChatListStore((state) => state.setChatList);

  useEffect(() => {
    if (chatListData?.items) {
      setChatList(chatListData.items);
    }
  }, [chatListData, setChatList]);

  const { chatId } = useParams();
  const {
    messages,
    pendingMessage,
    isStreaming,
    input,
    setMessages,
    setInput,
    sendMessage,
    cancelStreamingResponse,
  } = useChat();

  useEffect(() => {
    if (chatId) {
      (async () => {
        const { items } = await getChatDetail(chatId);
        setMessages(items);
      })();
    } else {
      setMessages([]);
    }
  }, [chatId, setMessages]);

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div className="relative flex h-screen overflow-hidden bg-white">
      <div
        className={`[&::-webkit-scrollbar-thumb]:[bg-none] box-border flex h-[calc(100vh-40px)] flex-1 flex-col items-center overflow-y-auto transition-all duration-300 [&::-webkit-scrollbar-thumb]:[background-color:lightgray] [&::-webkit-scrollbar-thumb]:[border-radius:8px] [&::-webkit-scrollbar]:[width:8px] ${messages.length === 0 ? 'justify-center' : 'relative mb-[40px] pt-[100px]'}`}
      >
        {messages.length === 0 && (
          <div className="mb-[24px] text-center">
            <h2 className="text-[32px] font-[600] text-[#5D5F62]">
              무엇을 도와드릴까요?
            </h2>
          </div>
        )}

        <div
          className={`absolute left-[calc(50%+76px/2)] z-30 min-h-fit w-full max-w-[800px] translate-x-[-50%] pb-[200px] ${
            messages.length === 0 ? '' : 'flex-1'
          }`}
        >
          {messages.map((m, i) => (
            <MessageItem key={i} chatMessage={m} />
          ))}

          {pendingMessage && (
            <MessageItem
              chatMessage={{
                role: 'assistant',
                content: { message: pendingMessage },
              }}
            />
          )}

          <div ref={bottomRef} />

          <div
            className={`${
              messages.length === 0
                ? 'flex items-center justify-center'
                : 'absolute bottom-0 left-0 w-full py-5'
            }`}
          ></div>
        </div>
      </div>
      <ChatInput
        input={input}
        setInput={setInput}
        isStreaming={isStreaming}
        onSend={() => sendMessage(input, chatId)}
        onCancel={cancelStreamingResponse}
      />
    </div>
  );
};
