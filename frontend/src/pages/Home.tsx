import { useEffect, useRef, useState } from 'react';

// import { getChatHistory } from '@/utils/chatStorage';

import { useChat } from '@/hooks/useChat';

import { ChatInput } from '@/components/ChatInput';
import { MessageItem } from '@/components/MessageItem';
import { Sidebar } from '@/components/Sidebar';

export const HomePage = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const {
    messages,
    pendingMessage,
    isStreaming,
    input,
    setInput,
    sendMessage,
    cancelStreamingResponse,
  } = useChat();

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]); // typingText 제외

  // useEffect(() => {
  //   const history = getChatHistory();
  //   setChatHistory(history);
  // }, [setChatHistory]); // setChatHistory를 의존성 배열에 추가

  // useEffect(() => {
  //   const history = getChatHistory();
  //   if (history.length > 0) {
  //     const last = history[history.length - 1];
  //     selectChat(last.id, last.messages);
  //   } else {
  //     startNewChat();
  //   }
  // }, []);

  return (
    <div className="flex h-screen bg-white">
      <div className="fixed right-[60px] top-[36px] z-50 flex items-center gap-[8px]">
        <div className="h-8 w-8 rounded-full bg-[#D9D9D9]" />
        <span className="text-[16px] font-[700] text-[#333534]">
          이용자 이름
        </span>
      </div>

      <Sidebar
        isSidebarOpen={isSidebarOpen}
        toggleSidebar={toggleSidebar}
        // startNewChat={startNewChat}
        // chatHistory={chatHistory}
        // onChatSelect={selectChat}
        startNewChat={() => {}}
        chatHistory={[]}
        onChatSelect={() => {}}
      />

      <div
        className={`ml-[76px] flex h-screen flex-1 flex-col items-center transition-all duration-300 ${messages.length === 0 ? 'justify-center' : 'relative pb-[200px] pt-[144px]'}`}
      >
        {messages.length === 0 && (
          <div className="mb-[24px] text-center">
            <h2 className="text-[32px] font-[600] text-[#5D5F62]">
              무엇을 도와드릴까요?
            </h2>
          </div>
        )}

        <div
          className={`w-full max-w-[800px] ${
            messages.length === 0 ? '' : 'flex-1 overflow-y-auto'
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
          >
            <ChatInput
              input={input}
              setInput={setInput}
              isStreaming={isStreaming}
              onSend={sendMessage}
              onCancel={cancelStreamingResponse}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
