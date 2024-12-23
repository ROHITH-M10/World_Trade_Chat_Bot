import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import News from './components/News';
import Chat from './components/Chat';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<News />} />
        <Route path="/chat/:id" element={<Chat />} />
      </Routes>
    </Router>
  );
}

export default App;
