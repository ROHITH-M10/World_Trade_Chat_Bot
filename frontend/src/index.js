import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
// import '../src/style.css';

const container = document.getElementById('root');
const root = createRoot(container); // Create the root
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);