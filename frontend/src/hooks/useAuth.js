import { useSyncExternalStore } from 'react';

import authService from '../services/authService';

function useAuth() {
  const user = useSyncExternalStore(
    authService.subscribe,
    authService.getCurrentUser,
    () => null
  );
  const token = user?.access || user?.token || null;

  return {
    user,
    token,
    isAuthenticated: Boolean(token),
    isAdmin: authService.isAdmin(user),
  };
}

export default useAuth;
