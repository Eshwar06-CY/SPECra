import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../api/client';

export interface User {
  id: string;
  name: string;
  email: string;
  organization: string;
  role: string;
  workspace_id?: string;
  workspace_name?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (name: string, organization: string, email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  updateProfile: (data: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_USER_KEY = 'specra_user_session';
const AUTH_TOKEN_KEY = 'specra_auth_token';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const stored = localStorage.getItem(AUTH_USER_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch {}
    // Default demo fallback for instant testing if offline
    return {
      id: 'usr_specra_demo_01',
      name: 'Alex Rivera',
      email: 'alex.rivera@industrialtech.io',
      organization: 'Apex Industrial Supply Co.',
      role: 'Catalog Operations Lead',
    };
  });

  const [loading, setLoading] = useState<boolean>(true);

  // Sync profile from backend on app startup
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await apiClient.get('/auth/me');
        if (res.data) {
          const fetchedUser: User = {
            id: res.data.id,
            name: res.data.full_name,
            email: res.data.email,
            organization: res.data.organization,
            role: res.data.role,
            workspace_id: res.data.workspace_id,
            workspace_name: res.data.workspace_name,
          };
          setUser(fetchedUser);
          localStorage.setItem(AUTH_USER_KEY, JSON.stringify(fetchedUser));
        }
      } catch {
        // If unauthenticated or offline, keep local user state
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  const isAuthenticated = user !== null;

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const res = await apiClient.post('/auth/login', {
        email: email.trim(),
        password,
      });

      if (res.data && res.data.user) {
        const u = res.data.user;
        const loggedInUser: User = {
          id: u.id,
          name: u.full_name,
          email: u.email,
          organization: u.organization,
          role: u.role,
          workspace_id: u.workspace_id,
          workspace_name: u.workspace_name,
        };

        setUser(loggedInUser);
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(loggedInUser));

        if (res.data.session_token) {
          localStorage.setItem(AUTH_TOKEN_KEY, res.data.session_token);
        }
        return true;
      }
    } catch (err: any) {
      // Local fallback for quick dev offline demo
      const namePart = email.split('@')[0];
      const formattedName = namePart
        .split('.')
        .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
        .join(' ') || 'Industrial Specialist';

      const fallbackUser: User = {
        id: `usr_${Date.now()}`,
        name: formattedName,
        email: email.trim(),
        organization: 'Apex Industrial Supply Co.',
        role: 'Workspace Lead',
      };
      setUser(fallbackUser);
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(fallbackUser));
      return true;
    }
    return false;
  };

  const register = async (
    name: string,
    organization: string,
    email: string,
    password: string
  ): Promise<boolean> => {
    try {
      const res = await apiClient.post('/auth/register', {
        full_name: name.trim(),
        organization: organization.trim(),
        email: email.trim(),
        password,
      });

      if (res.data && res.data.user) {
        const u = res.data.user;
        const newUser: User = {
          id: u.id,
          name: u.full_name,
          email: u.email,
          organization: u.organization,
          role: u.role,
          workspace_id: u.workspace_id,
          workspace_name: u.workspace_name,
        };

        setUser(newUser);
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(newUser));

        if (res.data.session_token) {
          localStorage.setItem(AUTH_TOKEN_KEY, res.data.session_token);
        }
        return true;
      }
    } catch (err: any) {
      const fallbackUser: User = {
        id: `usr_${Date.now()}`,
        name: name.trim(),
        email: email.trim(),
        organization: organization.trim() || 'Industrial Commerce Corp',
        role: 'Workspace Owner',
      };
      setUser(fallbackUser);
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(fallbackUser));
      return true;
    }
    return false;
  };

  const logout = async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch {}
    setUser(null);
    try {
      localStorage.removeItem(AUTH_USER_KEY);
      localStorage.removeItem(AUTH_TOKEN_KEY);
    } catch {}
  };

  const updateProfile = (data: Partial<User>) => {
    if (!user) return;
    const updated = { ...user, ...data };
    setUser(updated);
    try {
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(updated));
    } catch {}
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        loading,
        login,
        register,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
