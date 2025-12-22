import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { AccessibilityProvider } from '@/context/AccessibilityContext';
import { ThemeProvider } from '@/context/ThemeContext';
import { ModeProvider } from '@/context/ModeContext';
import '@/styles/global.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AccessibilityProvider>
        <ThemeProvider>
          <ModeProvider>
            <App />
          </ModeProvider>
        </ThemeProvider>
      </AccessibilityProvider>
    </BrowserRouter>
  </React.StrictMode>
);
