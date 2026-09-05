# Product Requirements Document (PRD)

## Project Name: Smart Chess - AI Mistake Coach

---

## 1. Executive Summary & Vision

**Smart Chess** is an interactive, real-time AI-assisted chess application designed to bridge the gap between playing chess and actively improving your game. Unlike traditional chess platforms that only analyze your game after it is finished, Smart Chess acts as a live **AI Mistake Coach**. It evaluates moves instantly using Stockfish 16, provides human-perspective feedback (e.g., *Book*, *Brilliant*, *Best*, *Excellent*, *Good*, *Inaccuracy*, *Mistake*, *Blunder*), highlights problematic moves in red, and offers an interactive pre-commit approval flow (*Play Anyway*, *Hint Box*, *Show Follow Up Moves*) so learners can analyze threats or retry moves before the bot responds. Additionally, the system continuously analyzes gameplay via Centipawn Loss to calculate the user's Tactical Performance Rating.

---

## 2. Target Audience

1. **Beginner to Intermediate Chess Players (Rating 400 - 1600)**:
   - Players who want to understand *why* a move was bad right when they play it, rather than waiting for post-game analysis.
   - Learners who benefit from visual arrows, square highlights, and plain-English move translations (e.g., *White Pawn to e4*).

2. **Self-Paced Chess Students & Coaches**:
   - Students looking for an interactive sandbox where they can retry moves, explore Stockfish-recommended lines, and see immediate punishment paths (*Show Follow Up Moves*).

3. **Casual Players Seeking Learner Assistance**:
   - Players who prefer an option to toggle **Learner Mode** on or off depending on whether they want visual assist arrows and piece suggestions.

---

## 3. Core Features & Functional Requirements

### 3.1 Interactive Board & Max-Sized Responsive Sizing
- **Max-Sized 8x8 Chessboard**: Scales up to `85vh` (up to `88vh` on 2K/4K displays), eliminating empty margin dead space.
- **Visual Styling**: Built with modern dark aesthetic (`#4a4a4a` / `#8a8a8a` square pattern), crisp bold black SVG coordinate labels (`a-h`, `1-8`), and smooth 150ms piece movement animations.
- **Dual Control Options**: Supports both **Drag-and-Drop** piece dragging and **Click-to-Move** (click source piece $\rightarrow$ green target dots $\rightarrow$ click destination).
- **Side Selection**: Toggle between **⚪ White** and **⚫ Black** side; board flips automatically and Stockfish engine plays the opposing color.
- **Clean Header Navigation Bar**: Top navigation bar displaying **You Vs Robot** mode label with an indented rating slider (**1320 - 3190 Rating Range**), **Side Selection**, **Restart Game**, **Learner Mode: ON/OFF**, **Coach Voice: ON/OFF**, and **Undo Move**.
- **Rating-Based Robot Opponent (1320 - 3190 Rating)**: Configurable Stockfish robot opponent driven by a separate, dedicated engine instance (`opponent_engine`) using native `UCI_LimitStrength` and `UCI_Elo` bounds (1320 to 3190).
- **Spoken Rating Announcement**: Web Speech API voice coach announces rating and tier (e.g., *"Rating 1500. Club Player mode."*) upon game creation.

### 3.2 Real-Time Stockfish 16 Engine Integration
- **Engine Analysis**: Backend communicates with Stockfish 16 at depth 14 with a **1.5-second time cap** per analysis line for millisecond centipawn evaluation (`score_cp`) and mate calculations without UI hangs.
- **Board Status Validation**: `_safe_analyse` pre-checks board validity (`board.status() == STATUS_VALID`) to prevent invalid FEN states from crashing the Stockfish UCI process.
- **Centipawn Loss Calculation**:
  $$\text{Centipawn Loss} = \text{Best Engine Move Eval} - \text{Played Move Eval}$$

### 3.3 Move Classification System
Every move played by the user is evaluated against Stockfish thresholds and labeled from the **User's Perspective**:

| Classification | Centipawn Loss Range / Criteria | UI Representation |
| :--- | :--- | :--- |
| **Book** | Known opening theory (Plies 1-3) | Neutral Badge |
| **Brilliant** | Tactical sacrifice yielding high evaluation | Bright Cyan Badge |
| **Best** | Matches Stockfish's top move ($0$ CP loss) | Green Badge |
| **Excellent** | $0 \le \text{CP Loss} \le 10$ | Green Badge |
| **Good** | $11 \le \text{CP Loss} \le 25$ | Soft Green Badge |
| **Inaccuracy** | $26 \le \text{CP Loss} \le 60$ | Yellow Badge + Orange/Red Destination Square |
| **Mistake** | $61 \le \text{CP Loss} \le 150$ | Orange Badge + Red Destination Square |
| **Blunder** | $> 150$ CP Loss | Red Badge + Red Destination Square |
| **Worst Move** | Blunder resulting in heavy material/mate loss | Dark Red Badge + Red Destination Square |

### 3.4 Coach Feedback & Red Square Highlight
- **Coach Feedback Header**: Displays move classification immediately after a move attempt.
- **Red Move Square Highlight**: When a move is classified as a *Mistake*, *Blunder*, or *Worst Move*, the destination square of the move is highlighted in **solid red** on the board.
- **Illegal Move Feedback**: Attempting an illegal move (e.g. moving a pinned piece) briefly pulses the target square in orange-red and displays a coach explanation (*"🔒 That piece is pinned! Moving it would expose your king to check."*).

### 3.5 Pre-Commit Approval & Move Controls
- **Good / Best / Book / Excellent Moves**: Commit immediately, updating the board FEN, speaking synchronized positive coach feedback, and playing move/capture sounds.
- **Mistake / Blunder / Worst Moves**: Pause in an **`Action Pending`** state with a red square highlight until the user decides.
- **Move Controls (3 Standardized Buttons)**:
  1. 💡 **Hint Box**: Highlights the starting square of the top-ranked engine move.
  2. ▶️ **Play Anyway**: Finalizes the pending move, commits to the backend engine, and triggers opponent response.
  3. 🛡️ **Show Follow Up Moves**: Automatically animates the engine's predicted refutation sequence (Principal Variation) on the board to demonstrate how the opponent will punish the mistake. The opponent's threatening piece is highlighted in blue, accompanied by a synchronized voice warning, before smoothly snapping back to the original position.
- **Top Header Undo Button**: **`Undo Move`** executes a full-stack rollback to retry your move.

### 3.6 Formatted Move Log
- **Human-Readable Moves**: Displays move history translated into verbose English with classification badges (e.g. `1. e4 Classic Opening | Pawn moves to e4`, `2. Nf3 Best Move 🌟 | Knight jumps to f3`).

### 3.7 Learner Mode Toggle & Arrow Visibility Rules
- **Learner Mode: ON**:
  - Automatically displays green recommendation dots/arrows on piece selection.
  - Automatically shows threat and alternative arrows when a Coach warning occurs.
- **Learner Mode: OFF**:
  - Suppresses all automatic arrows (piece selection and warning arrows are hidden).
  - **Arrows ONLY appear when the user explicitly clicks "Show Follow Up Moves"**.

### 3.8 Audio & Voice Features
- 🔊 **Classic Wooden Chess Sound Effects**: Powered by Web Audio API synthesizers (`playMoveSoundForUci()`) for piece placement and wooden captures.
- 🎙️ **Synchronized Coach Voice Narration**: Uses Web Speech API Text-to-Speech (`speakMoveCategory()`). Spoken audio is 100% synchronized with the committed Move Log badge classification (e.g., *Good* badge plays *"Good move."*, *Best* badge plays *"Best move on the board."*).

### 3.9 End-of-Game & Checkmate Announcements
- **Checkmate Detection**: Automatically detects checkmate states and displays a clear winner announcement: `🏆 Checkmate! [White/Black] wins the game!`.
- **Draw / Stalemate Detection**: Displays `🤝 Game Over! The game ended in a draw.`.
- **Post-Game Interaction**: Suppresses turn-attempt toasts after game over and prompts the user to start a new game.

### 3.10 Startup Auto-Retry & Resiliency
- **Auto-Retry Connection**: Frontend attempts up to 3 automatic retries (2-second interval) on startup to connect to the backend.
- **Interactive Connection Overlay**: If the backend is unreachable, a clean full-board overlay appears with a **🔄 Retry Connection** button instead of failing silently.

### 3.11 User Authentication & Payments (3-Minute Free Trial)
- **3-Minute Free Trial**: Unauthenticated or non-premium users are granted a 3-minute free gameplay trial. During this time, a persistent warning label is displayed (e.g., "You might end the game without login").
- **Paywall & Restart**: Exactly after 3 minutes, the free trial expires. The game is interrupted and restarts, forcing the user to log in and pay to continue playing or start new full games.
- **Google Authentication**: Users sign in via Supabase Auth (Google OAuth) to access their profile and payment status.
- **Razorpay Premium Paywall**: To bypass the 3-minute limit, users must purchase premium status via Razorpay. Upon successful checkout, the database is updated.

### 3.12 Enhanced Player Profile & Analytics System
- **Player Profile Modal (`ProfileDropdown.tsx`)**:
  - Dark glassmorphic design (`#111` background, `border-zinc-800`, top-right `X` close button).
  - Privacy-shielded identity: displays Player Name without exposing raw email addresses.
  - **3-Metric Key Grid**:
    1. **Performance Rating**: Trophy icon with dynamic tactical rating.
    2. **Win Rate**: TrendingUp icon showing live win percentage ($\frac{\text{Wins}}{\text{Completed Matches}} \times 100$) with match outcome breakdown (`${wins}W · ${losses}L · ${draws}D` or `No finished games`).
    3. **Total Games**: Static informational metric displaying total played games with `${totalCompleted} finished · ${activeGames} active` breakdown.
  - **Dedicated "View Analytics" Action**: Launches the dedicated Recharts Performance Statistics modal.
  - **Recent Games Continuation**: Lists up to the top 7 played games with interactive mini `<Chessboard>` thumbnails showing exact final FEN positions to click and resume.

- **Profile Editing & Vector Avatars (`ProfileEditModal.tsx` & `avatarUtils.tsx`)**:
  - **Display Name Editor**: Allows updating player in-game handle with length validation.
  - **Photo Upload**: Supports uploading custom photos from device gallery, auto-compressed client-side to base64 JPEG under 256px.
  - **12 Pure Vector SVG Chess Piece Avatars**: Complete set of 12 crisp vector piece icons (`wP`, `bP`, `wN`, `bN`, `wB`, `bB`, `wR`, `bR`, `wQ`, `bQ`, `wK`, `bK`), eliminating canvas/emoji rendering glitches on Windows and high-DPI displays.
  - **Multi-Tier Persistence (`useSession.ts`)**: Saves profile data simultaneously to Supabase Auth user metadata (`supabase.auth.updateUser`), `public.profiles` table upsert, and synchronous `localStorage` caching (`smartchess_profile_<userId>`), guaranteeing zero profile resets on browser refresh.

- **Custom Board Themes (`BoardThemeSelector.tsx`)**:
  - Theme Palette button positioned cleanly beside the white rook at the bottom-left corner of the chessboard (`-left-12 bottom-0`).
  - Supports 5 curated themes: Classic Wood, Midnight Blue, Emerald Green, Coral, and Obsidian with instant `localStorage` persistence.

- **Performance Trajectory Chart (`StatisticsModal.tsx`)**:
  - Powered by **Recharts (^3.10.1)** with pure vector SVG line charts.
  - Features dynamic responsive auto-fitting (`<ResponsiveContainer>`), subtle grid styling, and interactive hover tooltips displaying match index, opponent rating, and game outcome.

### 3.13 Match Continuation & Played Game Threshold
- **0-Move Filter**: Only games where **at least 1 move was made** (pawn or piece moved) are counted in Total Games and listed in Recent Games.
- **Auto-Cleanup**: Untouched starting-board sessions (0 moves) are automatically cleaned up from the database on new game creation and filtered out from API responses.
- **Top 7 Continuable Games**: Recent Games list strictly caps display to the 7 most recent played games for clean, focused continuation.
- **Puzzles Decoupling**: Tactical puzzles are stored in local SQLite (`puzzles2.db`) and never interfere with match win rates or Supabase game tables.

### 3.14 Dynamic Player Rating Prediction
- **Analytics Engine**: The backend continuously analyzes player moves, comparing accuracy and centipawn loss against Stockfish best moves.
- **Predicted ELO**: Based on performance history, the system calculates and displays a dynamic "Predicted Player Rating" that updates as games are completed.

---

## 4. Technical Stack & System Architecture

### 4.1 Technology Stack

- **Frontend**:
  - Framework: **Next.js 15 (App Router)** + **React 19** + **TypeScript**
  - Styling: **Tailwind CSS** (Dark Theme) + Vanilla CSS
  - Charting Engine: **Recharts (^3.10.1)** (Vector SVG)
  - Chess Board Render: **`react-chessboard`**
  - Game Logic Utilities: **`chess.js`**
  - Audio & Voice: **Web Audio API Synthesizer** + **Web Speech API TTS**
  - Icons: **Lucide React**
  - Backend Client: Supabase JS Client & Native Fetch REST API

- **Backend**:
  - Framework: **FastAPI** (Python 3.12)
  - Server: **Uvicorn** (Asynchronous ASGI with WatchFiles reload)
  - Engine Wrapper: **`python-chess`**
  - Chess Engine: **Stockfish 16.1** (Windows `.exe` / Linux x86_64 binary)
  - Database: **Supabase PostgreSQL** (`supabase-py` client) + **SQLite** (`puzzles2.db`)
  - Payments: **Razorpay Python SDK**

### 4.2 Folder Structure

```
Smart_Chess/
├── PRD.md
├── ARCHITECTURE.md
├── summary.txt
├── performance.txt
├── Backend/
│   ├── app/
│   │   ├── main.py            # FastAPI endpoints (/api/game, /api/user, /api/puzzles)
│   │   ├── engine.py          # Stockfish UCI wrapper with 30s timeout & automatic retry
│   │   ├── classifier.py      # Centipawn loss classification & opening book
│   │   ├── game_manager.py    # Game session state, move commit, undo & 0-move cleanup
│   │   ├── analytics.py       # ACPL-based tactical rating adjustment algorithms
│   │   ├── puzzle_manager.py  # SQLite puzzle loader and evaluation manager
│   │   └── schemas.py         # Pydantic request & response models
│   ├── data/
│   │   └── puzzles2.db        # SQLite puzzle dataset (ratings 600-2600)
│   ├── stockfish.exe          # Stockfish 16.1 engine binary
│   └── requirements.txt
├── Frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx     # Root Next.js layout
│   │   │   ├── page.tsx       # Root page mounting ChessApp
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

## 5. Deployment Strategy

The application is designed for independent, decoupled deployment:
- **Frontend**: Hosted on **Vercel** or any Next.js edge platform for global low-latency CDN delivery.
- **Backend**: Hosted on a dedicated Linux VPS or container platform (**Render**, **Railway**, **AWS**, or **DigitalOcean**) with full CPU core access for Stockfish UCI processing.
- **Database**: Cloud-hosted **Supabase PostgreSQL** with automated JWT-based Row Level Security.
