# Smart Chess - AI Mistake Coach & Tactical Trainer

**Smart Chess** is an interactive, real-time AI-assisted chess platform designed to bridge the gap between playing chess and actively improving your game. Unlike traditional chess platforms that only analyze games after they end, Smart Chess acts as a live **AI Mistake Coach** powered by Stockfish 16.1. It analyzes moves instantaneously, detects blunders, provides human-perspective voice and visual feedback, and provides a pre-commit approval workflow so learners can explore threats before finalizing a move.

---

## Key Features

### 1. Live AI Mistake Coach & Pre-Commit Approval Flow
- **Instant Centipawn Loss Analysis**: Stockfish 16.1 evaluates every move against top engine lines at depth 14 with a 1.5-second time cap.
- **Move Classification Badges**: Categorizes moves from the player's perspective (*Book*, *Brilliant*, *Best*, *Excellent*, *Good*, *Inaccuracy*, *Mistake*, *Blunder*, *Worst Move*).
- **Red Square Mistake Highlight**: Destructive moves pause in an `Action Pending` state, highlighting the destination square in solid red.
- **Interactive Move Controls**:
  - 💡 **Hint Box**: Highlights the starting square of the top-ranked engine line.
  - ▶️ **Play Anyway**: Confirms and commits the mistake to challenge your recovery skills.
  - 🛡️ **Show Follow Up Moves**: Animates the opponent's punishment refutation line on the board and highlights threats before snapping back.
  - ↩️ **Undo Move**: Full-stack rollback of move pairs to retry.

### 2. Player Profile & Recharts Performance Analytics
- **Glassmorphic Profile Modal**: Dark `#111` theme with privacy protection (raw email hidden, in-game handle displayed).
- **3-Metric Key Dashboard**:
  - **Performance Rating**: Dynamic tactical rating based on Centipawn loss (ACPL).
  - **Win Rate**: Computed dynamically from finished games with subtitle outcome breakdowns (`${wins}W · ${losses}L · ${draws}D` or `No finished games`).
  - **Total Games**: Displays played matches with active/finished counts.
- **Performance Trajectory Graph**: Built with **Recharts (^3.10.1)** using pure vector SVG line charts, responsive auto-scaling (`<ResponsiveContainer>`), and interactive hover tooltips.
- **Profile Customization**: Update display name, upload custom photos (auto-compressed client-side to base64 JPEG under 256px), or select from 12 vector SVG chess piece avatars.
- **Multi-Tier Persistence**: Profile data is saved across Supabase Auth user metadata, `public.profiles` Postgres table, and synchronous `localStorage` caching—preventing profile resets on page refresh.

### 3. Match Continuation & History (Top 7 Cap)
- **Played Game Threshold**: Only games where **at least 1 move was made** are saved as continuable active games. Empty starting boards (0 moves) are automatically purged.
- **Recent Games Continuation**: Displays up to the top 7 recent played matches with interactive mini `<Chessboard>` thumbnails to click and resume instantly.

### 4. Tactical Puzzles & Dedicated SQLite Database
- **Integrated Puzzle Mode**: Play tactical puzzles categorized by difficulty levels (1-5, ELO 600 - 2600).
- **Decoupled Architecture**: Puzzles run from a dedicated local SQLite database (`Backend/app/data/puzzles2.db`), completely decoupled from match win rates and the Supabase match table.

### 5. Custom Board Themes & Polish
- **5 Board Themes**: Classic Wood, Midnight Blue, Emerald Green, Coral, and Obsidian.
- **Dedicated Theme Palette**: Positioned cleanly beside the white rook at the bottom-left of the chessboard (`-left-12 bottom-0`).
- **Responsive Sizing**: Scales up to `85vh` with crisp vector SVG coordinates and smooth piece animations.

### 6. Voice Narration & Audio
- **Web Speech API TTS**: Natural spoken commentary synchronized 100% with the committed move classification badge.
- **Web Audio API Synthesizer**: Classic wooden piece movement and capture sound effects.

### 7. Authentication, Trial & Paywall
- **Supabase Auth**: Secure Google OAuth and Email/Password login.
- **3-Minute Free Trial**: Guest countdown timer (`TrialTimer.tsx`) with warning toasts.
- **Razorpay Integration**: Premium payment gateway unlocking unlimited matches and persistent database saving.

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | **Next.js 15 (App Router)**, **React 19**, **TypeScript**, **Tailwind CSS**, **Recharts (^3.10.1)**, **react-chessboard**, **chess.js**, **Lucide Icons** |
| **Backend** | **FastAPI**, **Python 3.12**, **Uvicorn (ASGI)**, **python-chess**, **Stockfish 16.1 UCI Engine** |
| **Database & Auth** | **Supabase PostgreSQL** (Auth, Profiles, Games), **SQLite** (Tactical Puzzles Dataset) |
| **Payments** | **Razorpay Python SDK** & Razorpay Client Checkout |

---

## Project Structure

```
Smart_Chess/
├── PRD.md                     # Comprehensive Product Requirements Document
├── ARCHITECTURE.md            # In-depth System Architecture & API Contracts
├── summary.txt                # Complete Changelog & Implementation History
├── performance.txt            # ACPL Tactical Rating formulas and ELO rules
├── Backend/
│   ├── app/
│   │   ├── main.py            # FastAPI REST endpoints & lifespan management
│   │   ├── engine.py          # Stockfish UCI engine wrapper (30s timeout & retry)
│   │   ├── classifier.py      # Centipawn loss math & opening theory rules
│   │   ├── game_manager.py    # Game state memory, move commits, and 0-move cleanup
│   │   ├── analytics.py       # Centipawn loss tactical rating prediction
│   │   ├── puzzle_manager.py  # SQLite puzzle loader and evaluation
│   │   └── schemas.py         # Pydantic request & response schemas
│   ├── data/
│   │   └── puzzles2.db        # SQLite puzzle dataset (ratings 600-2600)
│   ├── stockfish.exe          # Stockfish 16.1 engine binary
│   └── requirements.txt
├── Frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx     # Next.js Root Layout
│   │   │   ├── page.tsx       # Root Page mounting ChessApp
│   │   │   └── globals.css    # Dark mode & custom scrollbar styling
│   │   ├── components/
│   │   │   ├── ChessApp.tsx            # Master application state & top navigation
│   │   │   ├── ChessBoardArea.tsx      # Max-sized responsive board & arrow overlays
│   │   │   ├── BoardThemeSelector.tsx  # Board theme palette selector
│   │   │   ├── CoachOverlay.tsx        # Pre-commit warning card & action buttons
│   │   │   ├── ProfileDropdown.tsx     # 3-metric profile modal & recent games list
│   │   │   ├── ProfileEditModal.tsx    # Player name editor & avatar selector
│   │   │   ├── StatisticsModal.tsx     # Recharts SVG rating trajectory modal
│   │   │   ├── MoveLog.tsx             # Verbose move history & badges
│   │   │   └── TrialTimer.tsx          # 3-minute guest trial countdown
│   │   ├── services/
│   │   │   └── api.ts                  # REST API client with auto-retry
│   │   └── utils/
│   │       ├── avatarUtils.tsx         # 12 pure vector SVG chess pieces
│   │       ├── useSession.ts           # Multi-tier profile persistence hook
│   │       ├── chessTranslator.ts      # SAN to verbose English translator
│   │       ├── soundEffects.ts         # Web Audio API sound synthesizer
│   │       └── coachVoice.ts           # Web Speech API TTS voice narration
│   ├── package.json
│   └── next.config.ts
```

---

## Setup & Local Development

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+ (Python 3.12 recommended)
- Stockfish binary (`stockfish.exe` on Windows or `stockfish` on Linux/macOS)

### 1. Run the Backend
```bash
cd Backend
python -m venv venv
venv\Scripts\activate      # Windows: venv\Scripts\activate | macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
*Backend API will run at `http://127.0.0.1:8000` (docs at `http://127.0.0.1:8000/docs`).*

### 2. Run the Frontend
```bash
cd Frontend
npm install
npm run dev
```
*Frontend application will run at `http://localhost:3000`.*

---

## Documentation Links
- [Product Requirements Document (PRD)](PRD.md)
- [System Architecture Document](ARCHITECTURE.md)
- [Summary of Work & Changelog](summary.txt)
- [Tactical Performance Rating Calculations](performance.txt)
- [Supabase & Razorpay Configuration Guide](supabase_Googlauth_Razorpay)

