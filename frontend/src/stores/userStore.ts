import { create } from 'zustand';

import { fetchInstance } from '@/api/fetchInstance';

type UserInfo = {
  name: string;

  email: string;
  nickname?: string;
  profile_image_url?: string;

  created_at: Date;
  updated_at: Date;
};

interface UserInfoState {
  userInfo: UserInfo | null;
  isPending: boolean;

  loadUserInfo: () => Promise<void>;
  logout: () => Promise<boolean>;
}

export const useUserInfoStore = create<UserInfoState>((set) => ({
  userInfo: null,
  isPending: true,

  loadUserInfo: async () => {
    set((prev) => ({ ...prev, isPending: true }));
    fetchInstance
      .get('/api/v1/users/me')
      .then((res) => {
        // @ts-expect-error 타입 변환 안돼서 임시 처리
        set((prev) => ({ ...prev, userInfo: res, isPending: false }));
      })
      .catch((e) => {
        console.log(e);
        set((prev) => ({ ...prev, userInfo: null, isPending: false }));
      });
  },

  // true: 로그아웃 성공
  // false: 로그아웃 실패
  logout: async () => {
    const res = await fetchInstance.post('/api/v1/auth/logout');
    if (res.status === 200) {
      set((prev) => ({ ...prev, userInfo: null }));
      return true;
    }
    return false;
  },
}));
