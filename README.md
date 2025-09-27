🤖 C++ Assistant Chatbot

A LangGraph-powered chatbot built with FastAPI (backend) and Streamlit (frontend).
This assistant helps competitive programmers write, test, and debug C++ code by running snippets securely inside a Docker container.

📂 Project Structure
chatbot_project/
│
├── fastapi_app/
│   └── main.py          # FastAPI backend with LangGraph chatbot
│
├── streamlit_app/
│   └── main.py          # Streamlit frontend UI
│
├── .env                 # Environment variables (Google API key)
│
└── requirements.txt     # Python dependencies

⚙️ Installation & Setup
1. Clone the Repository
git clone https://github.com/yourusername/chatbot_project.git
cd chatbot_project

2. Create Virtual Environment
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
.venv\Scripts\activate       # Windows

3. Install Dependencies
pip install -r requirements.txt

4. Setup Environment Variables

Create a .env file in the root directory:

GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"

5. Run the FastAPI Backend
cd fastapi_app
uvicorn main:app --reload --port 8000


The backend will start at http://127.0.0.1:8000

6. Run the Streamlit Frontend

Open a new terminal and run:

cd streamlit_app
streamlit run main.py


The chatbot UI will open in your browser at http://localhost:8501

🚀 How It Works

Frontend (Streamlit)

Provides a clean chat interface.

Sends user queries and chat history to the backend.

Displays AI responses in real-time.

Backend (FastAPI + LangGraph)

Uses LangGraph to manage chatbot states and tool calls.

Integrates Google Gemini (via langchain_google_genai) as the LLM.

Includes a secure C++ code executor that:

Runs user-provided C++ code inside an isolated Docker container.

Returns execution output/errors.

Tool: C++ Executor

Takes a full C++ program as input.

Compiles and executes it in a temporary Docker container.

Sends back the standard output or error messages.

🖥️ Example Usage

Ask programming questions

User: How do I write a binary search in C++?
Assistant: Here's an example implementation...


Run code directly

User: Run this program:
#include <iostream>
using namespace std;
int main() {
    cout << "Hello, World!" << endl;
    return 0;
}


✅ Output:

Execution successful. Output:

Hello, World!

📦 Requirements

Python 3.9+

Docker installed and running

Google Gemini API Key

Install all dependencies with:

pip install -r requirements.txt

🛡️ Security Notes

Code execution is isolated inside Docker containers.

Temporary files and containers are automatically cleaned up.

Ensure Docker has enough resources allocated to handle code execution.

🔮 Future Improvements

Support for multiple languages (Python, Java, etc.)

Persistent chat history (database integration)

Syntax highlighting for code responses

Deployment with Docker Compose

📝 License

This project is open-source under the MIT License.
