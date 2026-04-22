import { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { ThemeState } from '@/types';

interface ThemeContextType extends ThemeState {
  setPrimaryColor: (color: string) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

type ThemeAction =
  | { type: 'SET_PRIMARY_COLOR'; payload: string }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_SIDEBAR_COLLAPSED'; payload: boolean };

const initialState: ThemeState = {
  primaryColor: '#44404f',
  sidebarCollapsed: false,
  isSidebarOpen: true,
};

function themeReducer(state: ThemeState, action: ThemeAction): ThemeState {
  switch (action.type) {
    case 'SET_PRIMARY_COLOR':
      return {
        ...state,
        primaryColor: action.payload,
      };
    case 'TOGGLE_SIDEBAR':
      return {
        ...state,
        sidebarCollapsed: !state.sidebarCollapsed,
        isSidebarOpen: !state.isSidebarOpen,
      };
    case 'SET_SIDEBAR_COLLAPSED':
      return {
        ...state,
        sidebarCollapsed: action.payload,
        isSidebarOpen: !action.payload,
      };
    default:
      return state;
  }
}

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [state, dispatch] = useReducer(themeReducer, initialState);

  // Initialize theme from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme_preferences');
    if (savedTheme) {
      try {
        const themePrefs = JSON.parse(savedTheme);
        if (themePrefs.primaryColor) {
          dispatch({ type: 'SET_PRIMARY_COLOR', payload: themePrefs.primaryColor });
        }
        if (themePrefs.sidebarCollapsed !== undefined) {
          dispatch({ type: 'SET_SIDEBAR_COLLAPSED', payload: themePrefs.sidebarCollapsed });
        }
      } catch (error) {
        console.error('Error loading theme preferences:', error);
      }
    }
  }, []);

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;

    // Update CSS custom property for primary color
    root.style.setProperty('--color-primary-dark', state.primaryColor);

    // Save to localStorage
    localStorage.setItem('theme_preferences', JSON.stringify(state));
  }, [state]);

  const setPrimaryColor = (color: string) => {
    dispatch({ type: 'SET_PRIMARY_COLOR', payload: color });
  };

  const toggleSidebar = () => {
    dispatch({ type: 'TOGGLE_SIDEBAR' });
  };

  const setSidebarCollapsed = (collapsed: boolean) => {
    dispatch({ type: 'SET_SIDEBAR_COLLAPSED', payload: collapsed });
  };

  const value: ThemeContextType = {
    ...state,
    setPrimaryColor,
    toggleSidebar,
    setSidebarCollapsed,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
