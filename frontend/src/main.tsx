import React from 'react';
import ReactDOM from 'react-dom/client';
import AppRoot from './AppRoot';
// Fonts are bundled, not fetched from Google, so the UI makes no outside requests.
import '@fontsource/manrope/500.css';
import '@fontsource/manrope/600.css';
import '@fontsource/manrope/700.css';
import '@fontsource/manrope/800.css';
import '@fontsource/nunito/400.css';
import '@fontsource/nunito/500.css';
import '@fontsource/nunito/600.css';
import '@fontsource/nunito/700.css';
import '@fontsource/nunito/800.css';
import '@fontsource/plus-jakarta-sans/300-italic.css';
import '@fontsource/plus-jakarta-sans/400-italic.css';
import './styles/globals.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppRoot />
  </React.StrictMode>
);
