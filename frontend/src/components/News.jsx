import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';  // Import useNavigate hook from react-router-dom
import '../styles/news.css';  // Import the News component styles

function News() {
  const [news, setNews] = useState([]); // State to store the fetched news articles
  const navigate = useNavigate();  // Initialize the navigate function

  // Fetch news from the Flask backend on component mount
  useEffect(() => {
    fetch('http://127.0.0.1:5000/news')  // URL to your Flask API endpoint
      .then((response) => response.json())
      .then((data) => {
        setNews(data);  // Set the fetched news data to the state
      })
      .catch((error) => {
        console.error('Error fetching news:', error);  // Handle any fetch errors
      });
  }, []);  // Empty dependency array means it runs once when the component mounts

  // Function to handle the button click and navigate to Chat page with article ID
  const handleButtonClick = (id) => {
    navigate(`/chat/${id}`);  // Pass the article ID as part of the URL
  };

  return (
    <div className="news-container">
      {news.map((article) => (
        <div key={article.id} className="news-card">
          <div className="news-title">{article.title}</div>
          <div className="news-summary">{article.summary}</div>
          <button 
            className="news-button" 
            onClick={() => handleButtonClick(article.id)}  // Trigger navigation on button click
          >
            Chat
          </button>
        </div>
      ))}
    </div>
  );
}

export default News;
