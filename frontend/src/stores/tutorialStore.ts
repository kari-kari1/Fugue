/**
 * Zustand store for tutorial/onboarding state.
 * Migrates legacy localStorage keys automatically.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Migrate legacy onboarding_completed keys at module init time (before hydration)
const legacyCompleted = (() => {
  try {
    return localStorage.getItem('onboarding_completed') === 'true'
        || localStorage.getItem('tutorial_mode') === 'false';
  } catch { return false; }
})();

interface TutorialState {
  tutorialMode: boolean;
  onboardingCompleted: boolean;
  currentTipIndex: number;
  setTutorialMode: (mode: boolean) => void;
  completeOnboarding: () => void;
  setTipIndex: (index: number) => void;
  resetTutorial: () => void;
}

export const useTutorialStore = create<TutorialState>()(
  persist(
    (set) => ({
      tutorialMode: false,
      onboardingCompleted: legacyCompleted,
      currentTipIndex: 0,
      setTutorialMode: (mode) => set({ tutorialMode: mode }),
      completeOnboarding: () => set({ onboardingCompleted: true }),
      setTipIndex: (index) => set({ currentTipIndex: index }),
      resetTutorial: () =>
        set({ tutorialMode: false, onboardingCompleted: false, currentTipIndex: 0 }),
    }),
    {
      name: 'tutorial-state',
      // Merge legacy state on hydration
      onRehydrateStorage: () => (state) => {
        if (state && !state.onboardingCompleted && legacyCompleted) {
          state.onboardingCompleted = true;
        }
      },
    }
  )
);
