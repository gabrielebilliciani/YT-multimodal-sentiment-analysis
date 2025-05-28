# Codebase: YouTube Video Sentiment Analyser

This directory contains the Python application for the YouTube Video Sentiment Analyser project. It leverages the YouTube Data API v3 and Google's Gemini AI to automatically find product review videos and perform advanced sentiment analysis on their content. The extracted insights are structured into a detailed JSON format and stored locally in an SQLite database.

## Project Structure

Full organisation is described in the main `README.md` file in the root directory of the repository. Below is a brief overview of the key components in this `codebase` directory:

**Key Components:**

*   **`main.py`**: Orchestrates fetching video information, analysis by Gemini, and storage.
*   **`config.py`**: Centralises configurations, including API key loading, database paths, lists of target YouTube channels/products, and Gemini prompt templates.
*   **`core/youtube_client.py`**: Searches and retrieves video metadata from YouTube.
*   **`core/gemini_client.py`**: Uses Gemini to analyse video content and generate structured JSON.
*   **`core/database_manager.py`**: Manages interactions with the local SQLite database.

## Setup

1.  **Install Dependencies:**
    Ensure you have Python 3.8+ installed. Then, install the necessary Python packages using pip:
    ```bash
    pip install google-api-python-client google-generativeai python-dotenv pymongo
    ```

2.  **Set Up API Keys:**
    This project requires API keys for both the YouTube Data API and the Gemini API.
    *   In this `codebase` directory, copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   Open the newly created `.env` file in a text editor.
    *   Replace the placeholder values with your actual API keys:
        ```env
        YOUTUBE_API_KEY="YOUR_YOUTUBE_DATA_API_V3_KEY_HERE"
        GEMINI_API_KEY="YOUR_GOOGLE_AI_STUDIO_GEMINI_API_KEY_HERE"
        ```
    *   **Important:** The `.env` file is listed in `.gitignore` and should **never** be committed to your version control system if it contains real API keys.

3.  **Configure Targets (Optional):**
    Review and modify `config.py` to set:
    *   `REVIEWER_CHANNELS` and `PRODUCTS_TO_ANALYZE`.
    *   `GEMINI_JSON_STRUCTURE_REQUEST` (the detailed JSON schema for Gemini).

## Running the Application (phase 1)

Ensure you are in the root directory of this repository, then navigate to the `codebase` directory:

```bash

From within this `codebase` directory, run the main script:

```bash
python main.py
```

The script will process configured videos, analyse them using Gemini, and save results to the `reviews_analysis.db` SQLite database (or the name specified in `config.py`) located in this `codebase` directory. Console logs will show progress and any errors.

## Running the Analysis (phase 2)

In order to run the second part of the analysis, please use:

```
python -m analysis.report_generator
```

working in the `codebase` directory.

## Output

The primary output is the data stored in the SQLite database. Each row in the `video_reviews` table contains the product name, video details, reviewer information, analysis timestamp, and the full JSON string output from Gemini.