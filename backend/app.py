import sqlite3
import requests
from flask import Flask, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from flask import request
from auth_key import API_KEY  # Import API_KEY from auth_key.py


app = Flask(__name__)
CORS(app)

# Database initialization (Creates the necessary tables)
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
        DROP TABLE IF EXISTS news
    ''')
    cursor.execute('''
        CREATE TABLE news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            summary TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Scrape news articles from the website
def scrape_news():
    URL = "https://indianexpress.com/about/world-trade-organization/"
    HEADERS = {'User-agent': 'Mozilla/5.0', 'Accept-Language': 'en-US, en;q=0.5'}

    try:
        webpage = requests.get(URL, headers=HEADERS)
        webpage.raise_for_status()  # Raise error for bad HTTP status codes
        soup = BeautifulSoup(webpage.content, "html.parser")

        # Find article links
        articles = soup.find_all('div', class_='details')
        article_links = [article.find('a', href=True)['href'] for article in articles if article.find('a', href=True)]

        # Extract title and description from each article
        for article_link in article_links:
            try:
                new_webpage = requests.get(article_link, headers=HEADERS)
                new_webpage.raise_for_status()
                new_soup = BeautifulSoup(new_webpage.content, "html.parser")
                title = get_title(new_soup)
                description = get_description(new_soup)

                # Save to database
                conn = sqlite3.connect('db.sqlite3')
                cursor = conn.cursor()
                cursor.execute('INSERT INTO news (title, description) VALUES (?, ?)', (title, description))
                conn.commit()
                conn.close()
                print(f"Inserted article: {title}")

            except requests.RequestException as e:
                print(f"Error fetching article from {article_link}: {e}")

    except requests.RequestException as e:
        print(f"Error scraping news: {e}")

# Extract title from the article page
def get_title(soup):
    try:
        title = soup.find("h1", {"id": "main-heading-article"}).text.strip()
    except AttributeError:
        title = ""
    return title

# Extract description from the article page
def get_description(soup):
    try:
        article = soup.find("div", {"id": "pcl-full-content"}).text.strip()
        article = article.replace("\n", "").replace("'", "'").split("Why should you buy our Subscription?")[0]
    except AttributeError:
        article = ""
    return article

# Query Hugging Face API for generating summary
def summary_query(payload):
    SUMMARY_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    try:
        response = requests.post(SUMMARY_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error generating summary: {e}")
        return None

# Generate and update summary for all news articles
def generate_summary():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT id, description FROM news')
    articles = cursor.fetchall()
    conn.close()

    for article in articles:
        try:
            article_id = article[0]
            description = article[1]
            payload = {"inputs": description}

            summary = summary_query(payload)
            if summary and isinstance(summary, list):
                summary_text = summary[0].get("summary_text", "")
                if summary_text:
                    conn = sqlite3.connect('db.sqlite3')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE news SET summary = ? WHERE id = ?', (summary_text, article_id))
                    conn.commit()
                    conn.close()
                    print(f"Generated summary for article with ID {article_id}")
                else:
                    print(f"No summary generated for article with ID {article_id}")
            else:
                print(f"Failed to generate summary for article with ID {article_id}")

        except Exception as e:
            print(f"Failed to generate summary for article with ID {article_id}: {e}")

# Function that combines scraping and summarization
def process_news():
    init_db()  # Initialize the database (run once)
    scrape_news()  # Scrape news articles from the web
    generate_summary()  # Generate summaries for the news articles

    # show all the news articles
    # conn = sqlite3.connect('db.sqlite3')
    # cursor = conn.cursor()
    # cursor.execute('SELECT * FROM news')
    # articles = cursor.fetchall()
    # conn.close()

    # for article in articles:
    #     print("article number: ", article[0])
    #     print("title: ", article[1])
    #     print("description: ", article[2])
    #     print("summary: ", article[3])
    #     print("\n")

# Route to process news articles
@app.route('/news', methods=['GET'])  
def get_news_route():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM news where summary is not null')
    articles = cursor.fetchall()
    conn.close()

    news_list = []
    for article in articles:
        news_list.append({
            "id": article[0],
            "title": article[1],
            "description": article[2],
            "summary": article[3]
        })

    return jsonify(news_list) 

@app.route('/chat-summary/<int:id>', methods=['GET'])
def current_chat_summary(id):
    try:
        # Fetch the article or content based on the provided ID
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('SELECT summary FROM news WHERE id = ?', (id,))
        article = cursor.fetchone()
        conn.close()

        if not article:
            return jsonify({"error": "Article not found"}), 404

        
        return jsonify({"summary": article[0]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        

@app.route('/chat/<int:id>', methods=['POST'])
def current_chat_bot(id):
    input = request.json.get("text")   # Get the input from the request

    if input is None:
        return jsonify({"error": "Invalid input"}), 400
    
    # Fetch the article or content based on the provided ID
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT summary FROM news WHERE id = ?', (id,))
    article = cursor.fetchone()
    conn.close()

    if not article:
        return jsonify({"error": "Article not found"}), 404

    # Query the Hugging Face API for question-answering
    payload = {
        "inputs": {
            "question": input,
            "context": article[0]
        }
    }
    response = qna_query(payload)
    response = response["answer"] if "answer" in response else "Sorry, I do not understand your question."
    
    return jsonify({"reply": response}), 200





def qna_query(payload):
    try:
        QNA_API_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased-distilled-squad"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.post(QNA_API_URL, headers=headers, json=payload)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

def process_news_route():
    try:
        process_news()
        return jsonify({"message": "News articles scraped and summaries generated successfully!"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    process_news()  # Start processing as soon as the application runs
    app.run(debug=True)
