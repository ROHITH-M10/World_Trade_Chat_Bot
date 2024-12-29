import sqlite3
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from bs4 import BeautifulSoup
import google.generativeai as genai
import re


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes



from auth_key import API_KEY  # Import API_KEY from auth_key.py
from auth_key import GEMINI_API_KEY  # Import GEMINI_API_KEY from auth_key.py

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
                #print(f"Inserted article: {title}")

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
# def summary_query(payload):
#     SUMMARY_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
#     headers = {"Authorization": f"Bearer {API_KEY}"}

#     try:
#         response = requests.post(SUMMARY_API_URL, headers=headers, json=payload)
#         response.raise_for_status()
#         return response.json()
#     except requests.RequestException as e:
#         print(f"Error generating summary: {e}")
#         return None

# Using Gemini API for generating summary

def news_summary_query(payload):
    # print(payload)

    try:
        # print("Generating summary...")
        
        geminiInput = f"""
            You are an advanced summarization model designed to provide concise, clear, and insightful summaries of global trade insights based on current trends and statistics.

            The following input contains detailed articles and reports on global trade, covering key developments, economic policies, trade agreements, market trends, and challenges faced by various countries and sectors.

            Your task is to:
            - Provide a high-level summary of the global trade landscape, including key statistics and notable trends.
            - Highlight major trade partnerships, agreements, and policies that impact international trade.
            - Summarize key challenges and opportunities faced by global exporters and importers, referencing specific countries or sectors where applicable.
            - Extract insights into emerging markets, high-growth sectors, and the impact of geopolitical events on trade flows.
            - Mention any significant regulatory changes, tariffs, or trade agreements discussed in the articles.
            - Keep the summary concise, accurate, and easy to understand, avoiding unnecessary technical details.
            - Limit the summary to no more than 200 words.

            Please return your summary as a single paragraph without any bold text or special formatting.

            Input Data:
            {payload["inputs"]}
        """



        response = model.generate_content(geminiInput)
        # print(response.text)
        return {"summary_text": response.text}

    except requests.RequestException as e:
        print(f"Error generating summary: {e}")
        return None


def summary_query(payload):
    # print(payload)

    try:
        # print("Generating summary...")
        geminiInput = f"""
            You are an advanced summarization model designed to provide concise, clear, and insightful summaries of trade data.

            The following input contains detailed trade statistics for a country in a specified year, including overall export and import values, key trade partners, top exported and imported products, trade by product groups, tariff rates, and development indicators.

            Your task is to:
            - Provide a high-level summary of the overall trade values and key statistics for the specified country and year.
            - Highlight the top five export and import partners with their respective trade values and percentages.
            - Summarize the top five exported and imported products at the HS6 digit level with trade values.
            - Offer insights into trade by product groups (e.g., raw materials, intermediate goods, consumer goods, and capital goods), mentioning export and import values and percentages.
            - Briefly explain the tariffs and development indicators for the country in the specified year, including GDP, trade balance, and trade as a percentage of GDP.
            - Keep the summary concise, accurate, and easy to understand, avoiding unnecessary details.
            - Limit the summary to no more than 200 words.

            Please return your summary as a single paragraph without any bold text or special formatting.

            Input Data:
            {payload["inputs"]}
        """



        response = model.generate_content(geminiInput)
        # print(response.text)
        return {"summary_text": response.text}

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
            payload = {
                "inputs": description
                }

            summary = news_summary_query(payload)
            #print(summary)
            if summary and "summary_text" in summary:
                # print(f"Generated summary for article with ID {article_id}")
                summary_text = summary["summary_text"]
                if summary_text:
                    #print(summary_text)
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
    response = news_qna_query(payload)
    response = response["answer"] if "answer" in response else "Sorry, I do not understand your question."
    
    return jsonify({"reply": response}), 200




# Hugging Face API for question-answering
# def qna_query(payload):
#     try:
#         QNA_API_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased-distilled-squad"
#         headers = {"Authorization": f"Bearer {API_KEY}"}
#         response = requests.post(QNA_API_URL, headers=headers, json=payload)
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         return {"error": f"Request failed: {str(e)}"}

# Using Gemini API for question-answering

def news_qna_query(payload):
    try:
        # print("Generating summary...")
        qa_prompt = f"""
            You are an advanced question-answering model designed to analyze and answer questions based on the content of news articles. 

            The following input contains the full text of a news article about global trade, including developments, policies, trade relationships, market trends, and challenges across different countries and sectors.

            Your task is to:
            1. Thoroughly analyze the provided news article to understand its content and context.
            2. Answer questions based on the article, focusing on the main ideas, specific details, and relevant insights.
            3. Provide clear, concise, and well-supported answers to questions about global trade, economic policies, trade agreements, challenges, and geopolitical factors.
            4. Ensure that your answers are directly tied to the content of the article and avoid making assumptions beyond the given context.

            Input Data:
            {payload["inputs"]["context"]}
            Question:
            {payload["inputs"]["question"]}
        """

        response = model.generate_content(qa_prompt)
        # print(response.text)
        return {"answer": response.text}

    except requests.RequestException as e:
        print(f"Error generating summary: {e}")
        return None



def qna_query(payload):
    try:
        print("Question", payload["inputs"]["question"])
        print("Context", payload["inputs"]["context"])

        # print("Generating summary...")
        qa_prompt = f"""
            You are an advanced question-answering model designed to provide detailed and accurate answers to questions based on the provided context. 

            The following input contains a summary of a news article about the World Trade Organization, including key information and insights. 

            Your task is to:
            1. Answer questions based on the provided context, focusing on the main points and details.
            2. Provide clear and concise answers to questions about the World Trade Organization and related topics.
            3. Ensure that your answers are accurate and relevant to the questions asked.
            4. Use the context provided to generate informative and insightful responses.

            Input Data:
            {payload["inputs"]["context"]}
            Question:
            {payload["inputs"]["question"]}
            """
        response = model.generate_content(qa_prompt)
        # print(response.text)
        return {"answer": response.text}

    except requests.RequestException as e:
        print(f"Error generating summary: {e}")
        return None




# World Integrated Trade Solution (WITS)

DESCRIPTION = ""

# get and post methods

@app.route('/country-stats', methods=['GET'])
def get_or_post_country_stats():
    global DESCRIPTION
    try:
        if request.method == 'GET':
            # Extract parameters from the query string
            country_code = request.args.get('countryCode')
            year = request.args.get('year')
            print(f"GET Request - Country code: {country_code}, Year: {year}")

            if not country_code or not year:
                return jsonify({"error": "Invalid input"}), 400
            
            # Generate the report
            report = scrape_country_code_and_year(country_code, year)
            #print(f"Generated report: {report}")

            # Generate summary
            payload = {
                "inputs": report
            }
            summary = summary_query(payload)
            DESCRIPTION = report
            return jsonify({"report": summary['summary_text']})

        elif request.method == 'POST':
            # Extract JSON data from the POST request
            data = request.get_json()
            country_code = data.get('countryCode')
            year = data.get('year')
            print(f"POST Request - Country code: {country_code}, Year: {year}")

            if not country_code or not year:
                return jsonify({"error": "Invalid input"}), 400

            # Generate the report
            report = scrape_country_code_and_year(country_code, year)
            # print(f"Generated report: {report}")

            # Generate summary
            summary = summary_query({"inputs": report})
            return jsonify({"report": summary['summary_text']})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


        
        
def scrape_country_code_and_year(country_code, year):
    print(f"Scraping data for {country_code} in the year {year}...")

    URL = f"https://wits.worldbank.org/CountryProfile/en/Country/{country_code}/Year/{year}/Summarytext"
    HEADERS = {'User-agent': 'Mozilla/5.0', 'Accept-Language': 'en-US, en;q=0.5'}

    webpage = requests.get(URL, headers=HEADERS)

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(webpage.content, "html.parser")

    full_data = soup.find_all("div", attrs={"class": "tab-content"})

    report = ""

    for data in full_data:
        cleaned_text = data.text.strip()
        cleaned_text = re.sub(r"\s+", " ", cleaned_text)  # Remove extra newlines
        report += cleaned_text + " "  # Add a space for clarity

    # print("Scraped report:")
    # print(report)
    return report  # Return plain text, not jsonify

# chat-about-stats

@app.route('/stats-chat', methods=['POST'])
def chat_about_stats():
    input = request.json.get("text")   # Get the input from the request
    global DESCRIPTION
    print(f"Received input: {input}")
    # print(f"DESCRIPTION: {DESCRIPTION}")

    if input is None:
        return jsonify({"error": "Invalid input"}), 400
    
    # Fetch the article or content based on the provided ID



    # Query the Hugging Face API for question-answering
    payload = {
        "inputs": {
            "question": input,
            "context": DESCRIPTION
                }
    }
    response = qna_query(payload)
    response = response["answer"] if "answer" in response else "Sorry, I do not understand your question."
    
    return jsonify({"reply": response}), 200


# End
def process_news_route():
    try:
        process_news()
        return jsonify({"message": "News articles scraped and summaries generated successfully!"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

if __name__ == '__main__':

    # Initialize the GenerativeAI model
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    process_news()  # Start processing as soon as the application runs

    app.run(debug=True)
