# Chess Video Generator

This repository contains a full-stack application dedicated to generating dynamic, fast-paced chess puzzle videos using Remotion and React.

## Project Structure
- **/Frontend**: A Next.js application that contains the interactive web client and UI for exploring puzzles.
- **/Video_Generator**: A standalone Remotion application dedicated to generating the short-form puzzle videos.
- **/Backend**: A Python FastAPI application that connects to a database to supply random chess puzzles to both the frontend and video generator.

## Video Generation Workflow

The core feature of this repository is the automated video generation pipeline.

### 1. Start the Backend
The video generator fetches random puzzles from the backend API.
```bash
cd Backend
uvicorn app.main:app --reload --port 8000
```

### 2. Generate a Video
Once the backend is running, you can automatically generate a high-energy chess video by running the build script in the `Video_Generator` folder.
```bash
cd Video_Generator
npm run build
```

### What Happens During Generation?
1. **Fetching**: The `build.js` script fetches a random puzzle sequence (FEN and UCI moves) from `http://127.0.0.1:8000/api/puzzles/random`.
2. **Intermediate Storage**: It stores the sequence into a temporary `moves.json` file.
3. **Rendering**: It triggers `npx remotion render` targeting the `ChessVideo.tsx` component.
4. **Output**: The video is rendered locally and automatically saved to the `Video_Generator/out/` directory with a unique timestamp.

### Video Features
- **Dynamic Board Animations**: Pieces smoothly slide across the board using custom Remotion interpolations rather than static jumps.
- **Narrative Pacing**: Includes hook phrases ("Can you find the winning move?"), a thinking timer countdown, and an outro scene.
- **Dynamic Highlights**: Start and end squares of the last played move are highlighted.
- **Synced Audio**: Text-to-speech intro audio, "Brilliant" voice overs, piece movement clacks, and victory sound effects perfectly synced to the frame.

## Technologies
- **Remotion**: Programmatic Video Generation
- **React-Chessboard**: Visual Board Rendering
- **Chess.js**: Move Validation and Logic
- **FastAPI**: Puzzle Data Source
