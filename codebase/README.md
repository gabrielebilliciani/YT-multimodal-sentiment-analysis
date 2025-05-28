# Codebase: YouTube Video Sentiment Analyser

This directory contains the Python application for the YouTube Video Sentiment Analyser project. It leverages the YouTube Data API v3 and Google's Gemini AI to automatically find product review videos and perform advanced sentiment analysis on their content. The extracted insights are structured into a detailed JSON format and stored locally in an SQLite database.

## Project Structure

The codebase is organised as follows:

*   [`main.py`](./main.py) - Main script to orchestrate the analysis process.
*   [`config.py`](./config.py) - Configuration (API keys loaded from `.env`, target lists, DB path, Gemini prompts).
*   [`.env.example`](./.env.example) - Template for the `.env` file (for API keys).
*   *(You create)* `.env` - For storing your actual API keys (GIT-IGNORED).
*   [`README.md`](./README.md) - This documentation file.
*   [`.gitignore`](./.gitignore) - Specifies intentionally untracked files for Git.
*   **`core/`** - Core business logic package:
    *   [`core/__init__.py`](./core/__init__.py)
    *   [`core/youtube_client.py`](./core/youtube_client.py) - Handles YouTube Data API v3 interactions.
    *   [`core/gemini_client.py`](./core/gemini_client.py) - Handles Google Gemini API interactions.
    *   [`core/database_manager.py`](./core/database_manager.py) - Manages SQLite database operations.
*   **`utils/`** - Utility functions and configurations package (optional):
    *   [`utils/__init__.py`](./utils/__init__.py)
    *   [`utils/logging_config.py`](./utils/logging_config.py) - (Optional) Centralised logging setup.

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

## Running the Application

From within this `codebase` directory, run the main script:

```bash
python main.py
```

The script will process configured videos, analyse them using Gemini, and save results to the `reviews_analysis.db` SQLite database (or the name specified in `config.py`) located in this `codebase` directory. Console logs will show progress and any errors.

For running the second part of the analysis, please use:

```
python -m analysis.report_generator
```

working in the `codebase` directory.

## Output

The primary output is the data stored in the SQLite database. Each row in the `video_reviews` table contains the product name, video details, reviewer information, analysis timestamp, and the full JSON string output from Gemini.