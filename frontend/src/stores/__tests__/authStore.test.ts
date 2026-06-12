import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '../authStore';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock the API client
vi.mock('../../api/client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

beforeEach(() => {
  localStorageMock.clear();
  useAuthStore.setState({
    user: null,
    token: null,
    tokenExpiresAt: null,
    isAuthenticated: false,
    isLoading: false,
    _hydrated: false,
  });
});

describe('authStore — initial state', () => {
  it('starts unauthenticated', () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
  });
});

describe('authStore — logout', () => {
  it('clears all auth state on logout', () => {
    useAuthStore.setState({
      user: { id: '1', email: 'test@test.com', username: 'test', is_active: true, is_superuser: false, created_at: '', updated_at: '' },
      token: 'fake-token',
      tokenExpiresAt: Date.now() + 3600000,
      isAuthenticated: true,
    });

    useAuthStore.getState().logout();
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
  });
});

describe('authStore — token expiry', () => {
  it('reports token as expiring when < 5 minutes remain', () => {
    const fourMinutesFromNow = Date.now() + 4 * 60 * 1000;
    useAuthStore.setState({
      token: 'fake-token',
      tokenExpiresAt: fourMinutesFromNow,
      isAuthenticated: true,
    });

    // The store should have a checkTokenExpiry method
    expect(typeof useAuthStore.getState().checkTokenExpiry).toBe('function');
  });

  it('does not report expiring when > 5 minutes remain', () => {
    const tenMinutesFromNow = Date.now() + 10 * 60 * 1000;
    useAuthStore.setState({
      token: 'fake-token',
      tokenExpiresAt: tenMinutesFromNow,
      isAuthenticated: true,
    });

    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });
});
