import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/chat.css';

function Chat() {
  const { id } = useParams();  // Extract the article ID from the URL
  const [text, setText] = useState('');
  const [summary, setSummary] = useState('');
  const [answers, setAnswers] = useState([]);
  const [error, setError] = useState('');


  // fetch the summary of the article with the given ID
  useEffect(() => {
    fetch(`http://127.0.0.1:5000/chat-summary/${id}`)
      .then((response) => response.json())
      .then((data) => {
        setSummary(data.summary);
      })
      .catch((error) => {
        console.error('Error fetching summary:', error);
      }
    );
  }, [id]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch(`http://127.0.0.1:5000/chat/${id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({text}),
      });

      if (!response.ok) {
        const errorData = await response.json();
        setError(errorData.error || 'Something went wrong');
        return;
      }

      const curAns = await response.json();

      // Update state to include new response while preserving previous messages
      setAnswers((prevAnswers) => [...prevAnswers, { question: text, response: curAns.reply }]);
      setText(''); // Clear input field after submission
    } catch (error) {
      setError('Failed to generate response');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Chat with the Bot</h1>
      </header>

      <div className="generate-space">
        <div className="welcome-sub-heading">
          <h2>Article Summary</h2>
          <p>{summary}</p>
          <h3>Ask the bot a question or say something to start chatting</h3>
          <p>Enter a prompt and click "Go" to chat with the bot</p>
        </div>
        {error && <p className="error-info" style={{ color: 'red' }}>{error}</p>}

        {/* Display chat history */}
        {answers.length > 0 && (
          <div className="chat-history">
            {answers.map((answer, index) => (
              <div key={index} className="chat-item">
                <p><strong>You:</strong> {answer.question}</p>
                <p><strong>Bot:</strong> {answer.response}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Input form */}
      <div className="prompt-form">
        <form onSubmit={handleSubmit}>
          <label>
            <input
              type="text"
              value={text}
              placeholder="Enter a prompt"
              onChange={(e) => setText(e.target.value)}
            />
          </label>
          <button type="submit">Go</button>
        </form>
      </div>
    </div>
  );
}

export default Chat;
