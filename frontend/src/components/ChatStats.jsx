import React, { useState, useEffect } from 'react';
import '../styles/stats.css';


function ChatStats() {
  const [text, setText] = useState('');
  const [year, setYear] = useState(2018);
  const [countryCode, setCountryCode] = useState('IND');
  const [summary, setSummary] = useState('');
  const [answers, setAnswers] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSummary();
  }, [countryCode, year]); // Dependency array ensures updates on input change

  const handleYearChange = (year) => {
    setYear(year);
    setAnswers([]); // Clear chat history on year change
  };

  const handleCountryCodeChange = (countryCode) => {
    setCountryCode(countryCode);
    setAnswers([]); // Clear chat history on country code change
  };

  const fetchSummary = async () => {
    console.log('Fetching summary for', countryCode, year);
    setError(''); // Clear previous errors

    try {
      const response = await fetch(
        `http://127.0.0.1:5000/country-stats?countryCode=${countryCode}&year=${year}`,
      );
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setSummary(data.report); // Use 'report' as returned by Flask
    } catch (err) {
      console.error('Error fetching summary:', err);
      setError('Failed to fetch stats. Please try again.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); // Reset error state

    try {
      const response = await fetch('http://127.0.0.1:5000/stats-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        setError(errorData.error || 'Something went wrong');
        return;
      }

      const curAns = await response.json();

      // Update state to include new response while preserving previous messages
      setAnswers((prevAnswers) => [
        ...prevAnswers,
        { question: text, response: curAns.reply },
      ]);
      setText(''); // Clear input field after submission
    } catch (err) {
      console.error('Error generating response:', err);
      setError('Failed to generate response');
    }
  };

  return (
    <div className="Chat">
      <a href="/" className="back-button">
        Back to News
      </a>
      <header className="Chat-header">
        <h1>Chat with the Bot</h1>
      </header>

      <div className="generate-space">
        <div className="welcome-sub-heading">
          <div className="select-option-country-code-year">
            {/* Drop down for country code */}
            <label className='country-code'>
              Country Code
              <select
                value={countryCode}
                onChange={(e) => handleCountryCodeChange(e.target.value)}
              >
                <option value="IND">IND</option>
                <option value="USA">USA</option>
                <option value="CHN">CHN</option>
                <option value="RUS">RUS</option>
                <option value="GBR">GBR</option>

              </select>
            </label>

            {/* Drop down for year */}

            <label className='year'>
              Year
              <select
                value={year}
                onChange={(e) => {handleYearChange(e.target.value);}}
              >
                <option value={2018}>2018</option>
                <option value={2019}>2019</option>
                <option value={2020}>2020</option>
                <option value={2021}>2021</option>
                <option value={2022}>2022</option>
              </select>
            </label>
          </div>

          <div className="about-article">
            Stats of {countryCode} in {year}
          </div>
          <div className="summary">{summary}</div>
          <p>Enter questions to chat with the bot about the article.</p>
        </div>
        {error && (
          <p className="error-info" style={{ color: 'red' }}>
            {error}
          </p>
        )}

        {/* Display chat history */}
        {answers.length > 0 && (
          <div className="chat-history">
            {answers.map((answer, index) => (
              <div key={index} className="chat-item">
                <div className="question">{answer.question}</div>
                <div className="answer">{answer.response}</div>
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

export default ChatStats;
