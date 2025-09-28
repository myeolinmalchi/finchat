import { fetchInstance } from './fetchInstance';

export interface MemoryListItem {
  content: string;
  memory_id: string;
  updated_at: string;
}

export interface MemoryListResponse {
  size: number;
  offset: number;
  items: MemoryListItem[];
}

// 메모리 목록 불러오기
export const getMemoryList = async (
  offset = 0,
  size = 20
): Promise<MemoryListResponse> => {
  return await fetchInstance.get('/api/v1/users/me/memories', {
    params: { offset, size },
  });
};

// 메모리 삭제
export const deleteMemory = async (
  memoryId: string,
): Promise<boolean> => {
  return await fetchInstance.delete(`/api/v1/users/me/memories/${memoryId}`);
};
