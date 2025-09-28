import { create } from 'zustand';

import { MemoryListItem, deleteMemory } from '@/api/memory';

interface MemoryListState {
  memoryList: MemoryListItem[];
  setMemoryList: (list: MemoryListItem[]) => void;
  deleteMemory: (memory_id: string) => Promise<void>;
}

export const useMemoryListStore = create<MemoryListState>((set) => ({
  memoryList: [],
  setMemoryList: (newList) => {
    set({ memoryList: newList });
  },
  deleteMemory: async (memory_id) => {
    deleteMemory(memory_id).then((isSuccess) => {
      if (isSuccess) {
        set((state) => ({
          memoryList: state.memoryList.filter(
            (memory) => memory.memory_id !== memory_id
          ),
        }));
      }
    });
  },
}));
