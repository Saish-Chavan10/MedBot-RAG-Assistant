MedBot: Enterprise RAG Medical Assistant 🩺

📌 Overview

MedBot is a production-grade, end-to-end Retrieval-Augmented Generation (RAG) application designed for healthcare professionals. It allows users to query a massive medical knowledge base (processing over 4,500+ pages of complex medical texts) using plain English, delivering highly accurate semantic search results with exact source citations.

Crucially, this system prioritizes data privacy by utilizing local LLM inference via Ollama (Qwen), ensuring sensitive medical queries are processed securely without relying on external, paid APIs.

🚀 Key Features

Privacy-First Local Inference: Utilizes the Qwen model running locally via Ollama, ensuring zero API costs and maximum data security (HIPAA-compliant architecture potential).

Enterprise-Grade RAG Pipeline: Processes complex PDFs, generates local embeddings, and securely stores 28,000+ vectors in Pinecone for rapid semantic retrieval.

Full-Stack Architecture: A responsive, interactive frontend built with Next.js, coupled with a robust, scalable backend powered by Python and Flask.

Real-Time Streaming: Implements advanced LLM text streaming for a seamless, low-latency user experience.

Secure Authentication & State Management: Integrated JWT authentication and Supabase (PostgreSQL) for user management and persistent chat history.

🛠️ Tech Stack

AI/ML: LangChain (LCEL), Ollama (Qwen 1.2), Local Embedding Models.

Backend: Python, Flask, Pinecone (Vector Database).

Frontend: Next.js, Tailwind CSS.

Database & Auth: Supabase (PostgreSQL), JWT.

DevOps & Deployment: Docker, Git.

⚙️ Local Setup & Installation

Prerequisites

Docker installed and running.

Ollama installed locally.

Python 3.10+ and Node.js (v18+) installed.

Pinecone and Supabase accounts for API keys.

1. Clone the Repository

git clone https://github.com/Saish-Chavan10/MedBot-RAG-Assistant.git
cd MedBot-RAG-Assistant


2. Setup Ollama (Local LLM)

Ensure Ollama is running and pull the required Qwen model:

ollama run qwen:1.2b  # Adjust tag based on the specific Qwen version you used


3. Backend Setup

Navigate to the backend directory, set up your virtual environment, and install dependencies:

cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt


Create a .env file in the backend directory with your database credentials (do not commit this file):

PINECONE_API_KEY=your_pinecone_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key


Start the Flask server:

flask run


4. Frontend Setup

Open a new terminal window, navigate to the frontend directory, and start the development server:

cd frontend
npm install
npm run dev


Access the application at http://localhost:3000.

🧠 Architecture Flow

User submits a medical query via the Next.js UI.

The Flask backend receives the request and utilizes a local embedding model to vectorize the query.

Pinecone Vector DB performs a similarity search across the 28k+ embedded medical document chunks.

Top context chunks are retrieved and passed to the local Qwen LLM via LangChain.

The LLM synthesizes a highly accurate response based only on the retrieved context (mitigating hallucinations).

The response is streamed back to the user UI in real-time.

Developed by Saish Chavan | [LinkedIn Profile] | [Portfolio/Website]
