import { useEffect } from 'react';

import { useMemoryListStore } from '@/stores/memeoryListStore';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { getMemoryList } from '@/api/memory';
import { MemoryListResponse } from '@/api/memory';

export const useMemoryList = () => {
  const { memoryList, setMemoryList, deleteMemory } = useMemoryListStore();
  const queryClient = useQueryClient();

  const {
    isLoading: isMemoryLoading,
    error: memoryLoadError,
    data,
  } = useQuery<MemoryListResponse>({
    queryKey: ['memoryList'],
    queryFn: () => getMemoryList(),
  });

  const {
    isPending: isMemoryDeletionPending,
    error: memoryDeletionError,
    mutate,
  } = useMutation({
    mutationFn: deleteMemory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memoryList'] });
    },
  });

  useEffect(() => {
    if (data) {
      setMemoryList(data.items);
    }
  }, [data, setMemoryList]);

  return {
    memoryList,
    deleteMemory: mutate,
    isMemoryLoading,
    memoryLoadError,
    isMemoryDeletionPending,
    memoryDeletionError,
  };
};
