import { getAuthHeaders, request } from './api';

const STORAGE_KEY = 'user';
const listeners = new Set();

const normalizeUser = (data) => {
  if (!data) {
    return null;
  }

  return {
    ...data,
    access: data.access || data.token,
    token: data.access || data.token,
  };
};

const readStoredUser = () => {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? normalizeUser(JSON.parse(stored)) : null;
  } catch {
    return null;
  }
};

let currentUser = readStoredUser();

const notifyAuthChange = () => {
  listeners.forEach((listener) => listener());
};

const storeUser = (user) => {
  const normalized = normalizeUser(user);

  currentUser = normalized;

  if (typeof window !== 'undefined') {
    if (normalized) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  notifyAuthChange();
  return normalized;
};

const register = async (userData) => {
  const data = await request(
    '/auth/register/',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    },
    'Signup failed'
  );

  return storeUser(data);
};

const login = async (userData) => {
  const data = await request(
    '/auth/login/',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    },
    'Login failed'
  );

  return storeUser(data);
};

const loginWithGoogle = async (payload) => {
  const data = await request(
    '/auth/google/',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
    'Google login failed'
  );

  return storeUser(data);
};

const getCurrentUser = () => currentUser;

const getAccessToken = () => getCurrentUser()?.access || null;

const isAuthenticated = () => Boolean(getAccessToken());

const isAdmin = (user = getCurrentUser()) => Boolean(user?.is_staff || user?.is_superuser);

const subscribe = (listener) => {
  listeners.add(listener);

  if (typeof window === 'undefined') {
    return () => {
      listeners.delete(listener);
    };
  }

  const handleStorage = (event) => {
    if (event.key && event.key !== STORAGE_KEY) {
      return;
    }

    currentUser = readStoredUser();
    listener();
  };

  window.addEventListener('storage', handleStorage);

  return () => {
    listeners.delete(listener);
    window.removeEventListener('storage', handleStorage);
  };
};

const refreshProfile = async (token = getAccessToken()) => {
  if (!token) {
    return null;
  }

  const profile = await request(
    '/auth/me/',
    {
      headers: getAuthHeaders(token),
    },
    'Failed to fetch profile'
  );

  const currentUser = getCurrentUser();
  if (!currentUser) {
    return null;
  }

  return storeUser({
    ...currentUser,
    ...profile,
    access: currentUser.access,
    refresh: currentUser.refresh,
  });
};

const logout = () => {
  currentUser = null;

  if (typeof window !== 'undefined') {
    localStorage.removeItem(STORAGE_KEY);
  }

  notifyAuthChange();
};

const authService = {
  register,
  login,
  loginWithGoogle,
  logout,
  getCurrentUser,
  getAccessToken,
  isAuthenticated,
  isAdmin,
  subscribe,
  refreshProfile,
  storeUser,
};

export default authService;
