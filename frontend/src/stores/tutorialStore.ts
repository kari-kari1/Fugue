/**
 * Zustand store for tutorial/onboarding state.
 * Replaces raw localStorage calls with a persisted store.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface TutorialState {
  /** Whether the in-app tutorial overlay mode is active */
  tutorialMode: boolean;
  /** Whether the onboarding wizard has been completed */
  onboardingCompleted: boolean;
  /** Current tip index in the tutorial overlay */
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
      onboardingCompleted: false,
      currentTipIndex: 0,

      setTutorialMode: (mode) => set({ tutorialMode: mode }),
      completeOnboarding: () => set({ onboardingCompleted: true }),
      setTipIndex: (index) => set({ currentTipIndex: index }),
      resetTutorial: () =>
        set({ tutorialMode: false, onboardingCompleted: false, currentTipIndex: 0 }),
    }),
    { name: 'tutorial-state' }
  )
);
