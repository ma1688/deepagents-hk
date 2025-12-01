import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { v4 as uuidv4 } from 'uuid';

interface UserState {
  userId: string;
  isInitialized: boolean;
  initializeUser: () => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set, get) => ({
      userId: '',
      isInitialized: false,
      
      initializeUser: () => {
        const { userId, isInitialized } = get();
        if (!isInitialized || !userId) {
          set({
            userId: uuidv4(),
            isInitialized: true,
          });
        }
      },
    }),
    {
      name: 'hkex-user-storage',
    }
  )
);

