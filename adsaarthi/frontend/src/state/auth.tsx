import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, clearToken, getToken, setToken } from "@/api/client";
import type { Brand, User } from "@/api/types";

interface AuthContextValue {
  user: User | null;
  brand: Brand | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (payload: {
    brand_name: string;
    category?: string;
    full_name: string;
    email: string;
    password: string;
  }) => Promise<void>;
  logout: () => void;
  refreshBrand: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [brand, setBrand] = useState<Brand | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadCurrentUser() {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    try {
      const [me, myBrand] = await Promise.all([api.get<User>("/auth/me"), api.get<Brand>("/brands/me")]);
      setUser(me);
      setBrand(myBrand);
    } catch {
      clearToken();
      setUser(null);
      setBrand(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCurrentUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function login(email: string, password: string) {
    const { access_token } = await api.post<{ access_token: string }>("/auth/login-json", { email, password });
    setToken(access_token);
    await loadCurrentUser();
  }

  async function signup(payload: {
    brand_name: string;
    category?: string;
    full_name: string;
    email: string;
    password: string;
  }) {
    const { access_token } = await api.post<{ access_token: string }>("/auth/signup", payload);
    setToken(access_token);
    await loadCurrentUser();
  }

  function logout() {
    clearToken();
    setUser(null);
    setBrand(null);
  }

  async function refreshBrand() {
    const myBrand = await api.get<Brand>("/brands/me");
    setBrand(myBrand);
  }

  return (
    <AuthContext.Provider value={{ user, brand, loading, login, signup, logout, refreshBrand }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
