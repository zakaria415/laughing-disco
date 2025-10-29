import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import re
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import psycopg2
from db_helpers import save_analysis_result # Import the saving function

# Download VADER lexicon if not already downloaded
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except nltk.downloader.DownloadError:
    nltk.download('vader_lexicon')

analyzer = SentimentIntensityAnalyzer()

async def fetch_page(session, url):
    """Fetches content from a single URL."""
    try:
        async with session.get(url) as response:
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            return await response.text()
    except aiohttp.ClientError as e:
        print(f"Error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching {url}: {e}")
        return None


def analyze_sentiment(text):
    """Analyzes the sentiment of a given text using VADER."""
    if not text:
        return 0.0 # Return neutral score for empty text
    score = analyzer.polarity_scores(text)
    return score['compound'] # Use the compound score as the overall sentiment


def extract_text(html_content):
    """Extracts text content from HTML."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()
    text = soup.get_text()
    # Clean up whitespace
    cleaned_text = re.sub(r'\s+', ' ', text).strip()
    return cleaned_text


async def scrape_and_analyze_single_page(session, url):
    """Scrapes a single page, extracts text, and analyzes sentiment."""
    html_content = await fetch_page(session, url)
    if html_content:
        text = extract_text(html_content)
        sentiment_score = analyze_sentiment(text)
        return {'url': url, 'sentiment_score': sentiment_score, 'text_content': text}
    return None


async def run_scraper(urls, concurrency):
    """Runs the scraper concurrently for a list of URLs."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            tasks.append(asyncio.ensure_future(scrape_and_analyze_single_page(session, url)))

        # Limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        async def sem_task(task):
            async with semaphore:
                return await task

        results = await asyncio.gather(*[sem_task(task) for task in tasks])
        return [result for result in results if result is not None]


def run_scraper_and_analysis(db_url, start_url, pages_to_scrape, concurrency):
    """
    Orchestrates the scraping and sentiment analysis process.
    This is the main function called from main.py.
    """
    print(f"Starting scraping and analysis for: {start_url}")
    print(f"Pages to scrape: {pages_to_scrape}")
    print(f"Concurrency level: {concurrency}")

    # --- Placeholder for finding subsequent pages ---
    # The actual implementation would involve fetching the start_url, parsing for links,
    # and intelligently selecting subsequent pages based on relevance and the pages_to_scrape limit.
    # For this placeholder, we'll just use the start_url and potentially a few dummy URLs.
    urls_to_scrape = [start_url]
    # Example: Add some dummy URLs for demonstration if pages_to_scrape > 1
    if pages_to_scrape > 1:
         for i in range(1, pages_to_scrape):
              urls_to_scrape.append(f"{start_url}/page{i}") # This is a placeholder, implement actual link discovery


    try:
        # Run the asynchronous scraper
        loop = asyncio.get_event_loop()
        if loop.is_running(): # If running in an environment like Colab/Jupyter
             import nest_asyncio
             nest_asyncio.apply()
             loop = asyncio.get_event_loop() # Get the patched loop


        results = loop.run_until_complete(run_scraper(urls_to_scrape, concurrency))

        print(f"Finished scraping. Found {len(results)} results.")

        # Process results and save to database
        for result in results:
            try:
                # Call the save_analysis_result function from db_helpers.py
                # Need to pass db_url to save_analysis_result as well
                save_analysis_result(db_url, result['url'], result['sentiment_score'], result['text_content'])
                print(f"Saved analysis for {result['url']}")
            except Exception as db_error:
                print(f"⚠️ Error saving analysis for {result['url']}: {db_error}")

    except Exception as e:
        print(f"⚠️ An error occurred during the scraping and analysis process: {e}")

    print("Scraping and analysis process finished.")

