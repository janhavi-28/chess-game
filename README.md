# Smart Chess - AI Mistake Coach

Smart Chess is an interactive, real-time AI-assisted chess application designed to bridge the gap between playing chess and actively improving your game. 

It evaluates moves instantly using Stockfish 16, provides human-perspective feedback (e.g., *Best*, *Mistake*, *Blunder*), and offers an interactive pre-commit approval flow so learners can analyze threats or retry moves before the bot responds.

## Features
- **Real-Time Stockfish Analysis**: Play against a rating-adjustable Stockfish opponent (1320 - 3190 ELO).
- **Interactive Move Coaching**: Get immediate feedback on your moves. If you blunder, the game pauses, highlights the mistake, and lets you ask for a hint, see the follow-up punishment, or undo.
- **Learner Mode**: Visual arrows and square highlights to guide your piece selection.
- **Voice Narration**: Web Speech API announces your move quality in real-time.
- **Authentication & Payments**: Integrated with **Supabase (Google Auth)** and **Razorpay** to require a premium unlock before playing.

## Project Structure
- **/Frontend**: A React 18 + TypeScript application built with Vite and Tailwind CSS.
- **/Backend**: A Python FastAPI application that manages the Stockfish engine and handles Razorpay order generation.

## Setup & Installation

Please refer to the detailed [Client Setup Guide (Supabase & Razorpay)](supabase_setup_guide.md) for instructions on how to initialize the database and connect your payment keys.

### 1. Run the Backend
```bash
cd Backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Run the Frontend
```bash
cd Frontend
npm install
npm run dev
```

## Documentation
- [Product Requirements Document (PRD)](prd.md)
- [Architecture Document](architecture.md)
- [Supabase & Razorpay Setup Guide](supabase_setup_guide.md)
