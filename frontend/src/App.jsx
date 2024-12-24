import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import News from './components/News';
import ChatNews from './components/ChatNews';
import ChatStats from './components/ChatStats';
import '../src/styles/style.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<News />} />
        <Route path="/stats" element={<ChatStats />} />
        <Route path="/chat/:id" element={<ChatNews/>} />
      </Routes>
    </Router>
  );
}

export default App;
