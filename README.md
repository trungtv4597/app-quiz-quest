# Quiz Quest Telegram Bot

## OVerview
This project is a studying initiative designed to practice and demonstrate skills in
* Building Telegram bots 
* And leveraging LlamaIndex for AI-driven applications.

## Project Structure
The project consists of 2 main Python scripts:
* [app.py](https://github.com/trungtv4597/app-quiz-quest/blob/master/src/app.py): Handles the Telegram bot interactions, manages the quiz game logic, and communicates with users via Telegram's API.
* [quiz_generator.py](https://github.com/trungtv4597/app-quiz-quest/blob/master/src/quiz_generator.py): Utilizes LlamaIndex to generate creative and unique quiz questions based on provided documents, ensuring each question is relevant for the game.


## Installation
1. Clone this repository to your local machine or download the scripts.
2. Install the required dependencies by running:
```bash
pip install -r requirements.txt
```
3. Create a new `global_settings.py` file to store global variables:
```python
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here"
TELEGRAM_GROUP_CHAT_ID = "your_group_chat_id_here"
TELEGRAM_PRIVATE_CHAT_IDS = ["private_chat_id_1", "private_chat_id_2"]  # For both partners
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_LLM = "gpt-3.5-turbo"  # or your preferred model
OPENAI_EMBED = "text-embedding-ada-002"  # or your preferred embedding model
STORAGE_PATH = "./storage"  # Directory for storing documents
INGESTION_FILE = "./cache.json"  # Cache file for ingestion
INDEX_PATH = "./index"  # Directory for index storage
QUIZ_FILE = "./quiz.csv"  # CSV file to store quiz questions
```
4. Ensure you have documents or data in the **STORAGE_PATH** directory that LlamaIndex can use to generate questions.