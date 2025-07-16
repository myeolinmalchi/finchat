// import { chatMock } from '@/mock/mock';
// import axios from 'axios';

// TODO: 삭제
// export interface ChatMessage {
//   role: 'user' | 'assistant' | string;
//   content: string | ChatContent[];
// }

// export interface ChatContent {
//   paragraph: string;
//   urls: string[];
// }

// export interface ChatRequest {
//   uuid: string;
//   question: string;
//   messages: ChatMessage[];
// }

// export interface ChatResponse {
//   title: string | null;
//   question: string;
//   answer: ChatContent[];
//   messages: ChatMessage[];
// }

// // const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
// const devMode = import.meta.env.DEV;

// export const sendChatMessage = async (
//   data: ChatRequest
// ): Promise<ChatResponse> => {
//   if (devMode) return chatMock;

//   const response = await axios.post<ChatResponse>(`/api/chat`, data);
//   // console.log(response.data);
//   return response.data;
// };

// TODO: new
export interface ChatRequestBody {
  chat_id?: string | null;
  message: string;
}

type ChatStatus = 'pending' | 'response' | 'stop' | 'failed';

export interface ChatProduct {
  product_type: string | null;
  description: string | null;
  institution: string | null;
  details: string | null;
  tags: string[] | null;
  options: { category: string; value: string }[] | null;
}

export interface ChatContent {
  message?: string;
  products?: ChatProduct[];
}

export interface SSEChatResponse {
  chat_id: string;
  status: ChatStatus;
  content: ChatContent | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: ChatContent;
}

export const createChatStream = (
  body: ChatRequestBody,
  onMessage: (data: SSEChatResponse) => void
) => {
  const controller = new AbortController();

  fetch(`/api/v1/chats`, {
    method: 'POST',
    body: JSON.stringify(body),
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('accessToken') || ''}`,
    },
    signal: controller.signal,
  }).then(async (res) => {
    const reader = res.body?.getReader();
    const decoder = new TextDecoder('utf-8');

    if (!reader) return;

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });

      chunk.split('\n').forEach((line) => {
        if (line.startsWith('data: ')) {
          const jsonString = line.replace('data: ', '').trim();
          if (jsonString === '[DONE]') {
            controller.abort();
            return;
          }

          try {
            const parsed: SSEChatResponse = JSON.parse(jsonString);
            onMessage(parsed);
          } catch (err) {
            console.error('파싱 오류', err);
          }
        }
      });
    }
  });

  return () => {
    controller.abort();
  };
};
