# Chess Video Generator

This repository contains a full-stack application dedicated to generating dynamic, fast-paced, "brainrot" style chess puzzle videos using Remotion and React.

## Project Structure
- **/Frontend**: A Next.js and Remotion application. This handles rendering the chess videos headless-ly.
- **/Backend**: A Python FastAPI application that connects to a database (or stockfish) to supply random chess puzzles to the frontend.

## Video Generation Workflow

The core feature of this repository is the automated video generation pipeline.

### 1. Start the Backend
The video generator fetches random puzzles from the backend API.
```bash
cd Backend
uvicorn app.main:app --reload --port 8000
```

### 2. Generate a Video
Once the backend is running, you can automatically generate a high-energy chess video by running the Remotion build script in the Frontend folder.
```bash
cd Frontend
npm run remotion:build
```

### What Happens During Generation?
1. **Fetching**: The `build-video.js` script fetches a random puzzle sequence (FEN and UCI moves) from `http://127.0.0.1:8000/api/puzzles/random`.
2. **Intermediate Storage**: It stores the sequence into a temporary `moves.json` file.
3. **Rendering**: It triggers `npx remotion render` targeting the `ChessVideo.tsx` component.
4. **Output**: The video is rendered locally and automatically saved to the `Frontend/public/videos/` directory with a unique timestamp. Windows File Explorer will automatically open this folder upon completion.

### Video Features
- **Brainrot Pacing**: Each move is paced exactly at 2.0s per move for optimal short-form content retention.
- **Dynamic Board Highlighting**: Start and end squares of moving pieces are automatically highlighted (Red for the opponent, Blue for the player).
- **Camera Shake**: A visceral camera shake effect emphasizes blunders early in the video.
- **Winning Zoom**: The camera dynamically zooms in when the winning move is played alongside a victory sound effect.
- **Meme Texts**: Displays high-retention hook text ("Bro thought he was winning... 😭" to "NAHHH 💀💀💀").

## Technologies
- **Remotion**: Programmatic Video Generation
- **React-Chessboard**: Visual Board Rendering
- **Chess.js**: Move Validation and Logic
- **FastAPI**: Puzzle Data Source
