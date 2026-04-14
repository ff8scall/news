---
image: "/images/posts/2026/04/14/fastapi-gemini-news-summarizer.jpg"
title: "[Practical Guide] Building a Real-Time News Summarizer Server using FastAPI and Gemini API"
date: "2026-04-14T10:28:32+09:00"
description: "A guide on building a backend server that periodically reads RSS feeds and performs real-time summarization and sentiment analysis of news articles using FastAPI and Gemini 1.5 Flash."
type: "posts"
clusters: ["guides"]
categories: ["tutorials"]
tags: ["guide", "tutorial"]
difficulty: "Advanced"
time_to_complete: "25 minutes"
image_prompt_core: "Glowing crystalline neural nodes connected by thin data streams, neon blue and deep purple, representing complex information flow in a zero-gravity, abstract 3D environment."
---

## 🎯 Overview
This guide covers how to build a real-time information processing system by combining the powerful text understanding capabilities of the latest LLM (Gemini 1.5 Flash) with a Python FastAPI backend. Specifically, the goal is to implement an endpoint that takes news from external RSS feeds and, instead of just passing raw text, receives structured outputs for **Summarization** and **Sentiment Analysis** via the Gemini API.

## 🚀 Phase 1. Infrastructure Setup and Environment Configuration
First, we set up the project environment and install the necessary libraries.

*   **Step 1-1. Create Project Directory and Activate Virtual Environment**
    *   `mkdir news-summarizer`
    *   `cd news-summarizer`
    *   `python3 -m venv venv`
    *   `source venv/bin/activate`
    *   **Expected Result:** The `(venv)` prompt is activated, allowing you to work within the virtual environment.

*   **Step 1-2. Install Required Libraries**
    *   We need FastAPI, Uvicorn (the server), the Gemini SDK, and `feedparser` for RSS parsing.
    *   `pip install fastapi uvicorn google-genai feedparser pydantic`
    *   **Expected Result:** All necessary packages are successfully installed, which can be confirmed using the `pip list` command.

*   **Step 1-3. Set Environment Variables (API Key)**
    *   For security, API keys should be managed as environment variables.
    *   `export GEMINI_API_KEY="YOUR_API_KEY_HERE"`
    *   **Expected Result:** `GEMINI_API_KEY` is set in the terminal session, allowing the Python code to make API calls. (You must replace this with your actual key.)

## 💡 Phase 2. Implementing Core Logic (Gemini API Integration and RSS Parsing)
Create a `main.py` file and implement the core data processing logic. This logic fetches data from the RSS feed and passes it to the Gemini API along with a structured prompt.

*   **Step 2-1. Basic Structure and Gemini Client Initialization**
    *   `touch main.py`
    *   Write the following code to `main.py` (Initializes the Gemini client and loads environment variables).

    ```python
    import os
    from google import genai
    from feedparser import parse
    from pydantic import BaseModel, Field
    
    # The API Key must be set as an environment variable.
    try:
        client = genai.Client()
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
        exit()
    ```
    *   **Expected Result:** The code executes without error, and the `client` object is successfully initialized.

*   **Step 2-2. Defining the Output Structure (Pydantic Schema)**
    *   We define a Pydantic model so that Gemini responds with a consistent JSON structure. This ensures type stability for the endpoint's return type.
    *   Add this to `main.py`.

    ```python
    # Defines the structure for news summarization and analysis.
    class ArticleAnalysis(BaseModel):
        summary: str = Field(description="A concise summary of the article's main points.")
        source: str = Field(description="The original source or publication of the information.")
        sentiment: str = Field(description="The overall emotional tone detected (e.g., Positive, Negative, Neutral).")
    ```

*   **Step 2. (The Core Logic):**
    *   This function simulates the core AI analysis process, taking raw feed data and returning structured results.

```python
# Placeholder function to simulate the core logic
def analyze_article(feed_data: str) -> list[dict]:
    """
    Receives feed data, analyzes it using AI, and returns structured data.
    """
    # In a real scenario, the Gemini API call logic would go here.
    print("--- Running AI Analysis Logic ---")
    return [
        {
            "summary": "The core content has been summarized.",
            "source": "News Source A",
            "sentiment": "Positive"
        }
    ]
```

*   **Step 2. (The Execution Function):**
    *   This function orchestrates the process: fetching the feed, calling the analyzer, and returning the result.

```python
def process_feed(feed_url: str) -> list[dict]:
    """
    Fetches data from a given feed URL, performs analysis, and returns the results.
    """
    # 1. Fetch feed data (In a real scenario, use the requests library)
    print(f"Fetching data from '{feed_url}'...")
    raw_data = "Dummy news feed data..."

    # 2. Perform analysis
    analyzed_results = analyze_article(raw_data)

    # 3. Return results
    return analyzed_results
```