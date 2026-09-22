import { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [isLight, setIsLight] = useState(() => {
    const saved = localStorage.getItem('ocean-theme');
    if (saved) return saved === 'light';
    // By default, default to dark mode for OceanAtlas
    return false;
  });

  useEffect(() => {
    if (isLight) {
      document.documentElement.classList.add('light');
      localStorage.setItem('ocean-theme', 'light');
    } else {
      document.documentElement.classList.remove('light');
      localStorage.setItem('ocean-theme', 'dark');
    }
  }, [isLight]);

  const toggleTheme = () => setIsLight(!isLight);

  return (
    <ThemeContext.Provider value={{ isLight, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
