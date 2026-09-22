import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);
const JWT_SECRET = 'ocean-atlas-dev-secret';

function encodeBase64Url(value) {
  const encoded = btoa(value);
  return encoded.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function generateMockJwt(email) {
  const header = { alg: 'HS256', typ: 'JWT' };
  const payload = {
    sub: email,
    role: 'operator',
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 60 * 60 * 24,
  };

  const headerSegment = encodeBase64Url(JSON.stringify(header));
  const payloadSegment = encodeBase64Url(JSON.stringify(payload));
  const signingInput = `${headerSegment}.${payloadSegment}`;
  const signature = encodeBase64Url(
    Array.from(new Uint8Array(
      new TextEncoder().encode(`${signingInput}.${JWT_SECRET}`)
    )).map((byte) => String.fromCharCode(byte)).join('')
  );

  return `${signingInput}.${signature}`;
}

export function useAuth() {
  return useContext(AuthContext);
}

// Mock Authentication Provider for UI Testing
export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load mock user from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('ocean_atlas_mock_user');
    if (storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        // Automatically refresh token on load to avoid 403 Forbidden on expired tokens
        parsedUser.token = generateMockJwt(parsedUser.email);
        localStorage.setItem('ocean_atlas_mock_user', JSON.stringify(parsedUser));
        setCurrentUser(parsedUser);
      } catch {
        localStorage.removeItem('ocean_atlas_mock_user');
      }
    }
    setLoading(false);
  }, []);

  function signup(email, password, displayName) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const cleanEmail = String(email || '').trim().toLowerCase();
        const cleanPassword = String(password || '').trim();

        if (!cleanEmail || !cleanPassword) {
          reject({ code: 'auth/invalid-credential' });
          return;
        }

        const newUser = {
          email: cleanEmail,
          displayName: displayName?.trim() || cleanEmail.split('@')[0],
          uid: 'mock-uid-' + Date.now(),
          token: generateMockJwt(cleanEmail),
        };

        localStorage.setItem('ocean_atlas_mock_user', JSON.stringify(newUser));
        setCurrentUser(newUser);
        resolve({ user: newUser });
      }, 600);
    });
  }

  function login(email, password) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const cleanEmail = String(email || '').trim().toLowerCase();
        const cleanPassword = String(password || '').trim();

        if (!cleanEmail || !cleanPassword) {
          reject({ code: 'auth/invalid-credential' });
          return;
        }

        const storedUser = localStorage.getItem('ocean_atlas_mock_user');
        if (storedUser) {
          const user = JSON.parse(storedUser);
          if (user.email === cleanEmail) {
            const refreshedUser = {
              ...user,
              token: generateMockJwt(cleanEmail),
            };
            localStorage.setItem('ocean_atlas_mock_user', JSON.stringify(refreshedUser));
            setCurrentUser(refreshedUser);
            resolve({ user: refreshedUser });
            return;
          }
        }

        const fallbackUser = {
          email: cleanEmail,
          displayName: cleanEmail.split('@')[0],
          uid: 'mock-uid-' + Date.now(),
          token: generateMockJwt(cleanEmail),
        };

        localStorage.setItem('ocean_atlas_mock_user', JSON.stringify(fallbackUser));
        setCurrentUser(fallbackUser);
        resolve({ user: fallbackUser });
      }, 600);
    });
  }

  function logout() {
    return new Promise((resolve) => {
      setTimeout(() => {
        localStorage.removeItem('ocean_atlas_mock_user');
        setCurrentUser(null);
        resolve();
      }, 400);
    });
  }

  const value = { currentUser, signup, login, logout };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}
