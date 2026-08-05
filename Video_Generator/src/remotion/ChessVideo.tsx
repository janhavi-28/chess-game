import React, { useMemo } from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, Sequence, Audio, staticFile, interpolate, spring, Img } from 'remotion';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';

export const ChessVideo: React.FC<{ moveList: string[], initialFen?: string }> = ({ moveList, initialFen }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Scene timings
  const hookDuration = 90;
  const thinkDuration = 90;
  const revealDuration = 60;
  const replayDuration = 300; // Time for the remaining moves
  const animFrames = 8; // Faster sliding animation (was 15)

  // Pre-calculate all FENs and move data
  const moveData = useMemo(() => {
    const c = new Chess(initialFen || undefined);
    const data = [];
    data.push({ fen: c.fen(), move: null, piece: null });
    
    for (const moveStr of moveList) {
      try {
        let m;
        // Parse raw from/to
        if (moveStr.length >= 4 && !moveStr.includes('+') && !moveStr.includes('x') && !moveStr.includes('-')) {
          const from = moveStr.substring(0, 2);
          const to = moveStr.substring(2, 4);
          const promotion = moveStr.length > 4 ? moveStr.substring(4) : undefined;
          
          // Get piece on source square BEFORE we make the move
          const pieceObj = c.get(from as any);
          
          m = c.move({ from, to, promotion });
          data.push({ fen: c.fen(), move: m, piece: pieceObj });
        } else {
          // It's SAN or UCI, we can parse it if we just use move()
          const beforeFen = c.fen();
          m = c.move(moveStr);
          // Get piece from the square it originated from using a temporary chess instance
          const tempC = new Chess(beforeFen);
          const pieceObj = tempC.get(m.from);
          data.push({ fen: c.fen(), move: m, piece: pieceObj });
        }
      } catch (e) {
        break; // Stop parsing if there's an illegal move
      }
    }
    return data;
  }, [initialFen, moveList]);

  // Pre-calculate the exact start frame for every move
  const moveTimings = useMemo(() => {
    return moveData.slice(1).map((_, index) => {
      if (index === 0) return 15;
      if (index === 1) return hookDuration + thinkDuration;
      const movesLeft = Math.max(1, moveList.length - 2);
      const framesPerRemainingMove = replayDuration / movesLeft;
      return Math.floor(hookDuration + thinkDuration + revealDuration + ((index - 2) * framesPerRemainingMove));
    });
  }, [moveData, hookDuration, thinkDuration, revealDuration, replayDuration, moveList.length]);

  // Determine which move is currently active/animating, if any
  let activeMoveIndex = -1;
  let isAnimating = false;
  let currentFen = moveData[0].fen;
  
  for (let i = moveTimings.length - 1; i >= 0; i--) {
    const startF = moveTimings[i];
    if (frame >= startF) {
      if (frame < startF + animFrames) {
        activeMoveIndex = i;
        isAnimating = true;
        currentFen = moveData[i].fen; // Display PRE-move board
      } else {
        currentFen = moveData[i + 1].fen; // Display POST-move board
      }
      break;
    }
  }

  // Set up variables for custom overlay rendering
  const isBlackBottom = initialFen && initialFen.includes(' w ') ? true : false;
  const boardWidth = 900;
  const squareSize = boardWidth / 8;
  
  const getSquarePos = (sq: string) => {
    const file = sq.charCodeAt(0) - 'a'.charCodeAt(0);
    const rank = parseInt(sq[1]) - 1;
    
    if (isBlackBottom) {
      return { x: (7 - file) * squareSize, y: rank * squareSize };
    } else {
      return { x: file * squareSize, y: (7 - rank) * squareSize };
    }
  };

  const animatingMove = isAnimating && activeMoveIndex !== -1 ? moveData[activeMoveIndex + 1] : null;
  const animStartFrame = activeMoveIndex !== -1 ? moveTimings[activeMoveIndex] : 0;
  
  // Highlight squares based on the last completed or currently active move
  const customSquareStyles: any = {};
  if (activeMoveIndex !== -1) {
    const lastM = moveData[activeMoveIndex + 1].move;
    if (lastM) {
      customSquareStyles[lastM.from] = { backgroundColor: 'rgba(255, 255, 0, 0.4)' };
      customSquareStyles[lastM.to] = { backgroundColor: 'rgba(255, 255, 0, 0.4)' };
    }
  }

  // Animations
  const boardScale = interpolate(frame, [0, hookDuration], [1, 1.05], { extrapolateRight: 'clamp' });
  const hookOpacity = interpolate(frame, [0, 15, hookDuration - 15, hookDuration], [0, 1, 1, 0]);
  const hookY = spring({ frame, fps, config: { damping: 12 } }) * 20;

  const thinkOpacity = interpolate(frame - hookDuration, [0, 15, thinkDuration - 15, thinkDuration], [0, 1, 1, 0]);
  
  let countdownText = "";
  const framesInThink = frame - hookDuration;
  if (framesInThink >= 0 && framesInThink < thinkDuration) {
    if (framesInThink < 30) countdownText = "3";
    else if (framesInThink < 60) countdownText = "2";
    else countdownText = "1";
  }

  const revealOpacity = interpolate(frame - (hookDuration + thinkDuration), [0, 15, revealDuration - 15, revealDuration], [0, 1, 1, 0]);
  
  const scene5Start = hookDuration + thinkDuration + revealDuration + replayDuration;
  const outroOpacity = interpolate(frame - scene5Start, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
  const fadeOutOpacity = interpolate(frame, [630, 660], [1, 0], { extrapolateRight: 'clamp' });

  // Custom pieces logic to hide the piece currently being animated
  const customPieces = useMemo(() => {
    if (!animatingMove || !animatingMove.move || !animatingMove.piece) return undefined;
    
    // The piece type string (e.g. 'wP' or 'bN')
    const color = animatingMove.piece.color;
    const type = animatingMove.piece.type.toUpperCase();
    const pieceKey = `${color}${type}` as any;
    
    return {
      [pieceKey]: ({ square, squareWidth }: any) => {
        // If this is the square the piece is starting from, hide it!
        if (square === animatingMove.move!.from) {
          return <div style={{ width: squareWidth, height: squareWidth }} />;
        }
        // Otherwise, render a standard transparent img tag requesting it fall back to react-chessboard defaults 
        // Note: react-chessboard doesn't have a simple fallback if a key is provided, so we manually render the SVG
        return (
          <img 
            src={staticFile(`assets/pieces/${pieceKey}.svg`)} 
            style={{ width: squareWidth, height: squareWidth }} 
          />
        );
      }
    };
  }, [animatingMove]);

  return (
    <AbsoluteFill style={{ backgroundColor: '#09090b', opacity: fadeOutOpacity }}>
      
      {/* Dynamic Texts overlaying the top */}
      <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start', paddingTop: '150px', zIndex: 10 }}>
        
        {/* Scene 1 Text */}
        <div style={{ position: 'absolute', opacity: hookOpacity, transform: `translateY(${hookY}px)` }}>
          <h1 style={{ color: 'white', fontSize: '60px', fontWeight: 'bold', textAlign: 'center', fontFamily: 'sans-serif' }}>
            ♟️ Can you find the winning move?
          </h1>
        </div>

        {/* Scene 2 Text */}
        <div style={{ position: 'absolute', opacity: thinkOpacity, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <h1 style={{ color: 'white', fontSize: '60px', fontWeight: 'bold', fontFamily: 'sans-serif' }}>Think...</h1>
          <h2 style={{ color: '#ffb703', fontSize: '90px', fontWeight: 'bold', fontFamily: 'sans-serif', margin: 0 }}>{countdownText}</h2>
        </div>

        {/* Scene 3 Text */}
        <div style={{ position: 'absolute', opacity: revealOpacity }}>
          <h1 style={{ color: '#00b4d8', fontSize: '70px', fontWeight: 'bold', fontFamily: 'sans-serif' }}>
            Brilliant!
          </h1>
        </div>

        {/* Scene 5 Text */}
        <div style={{ position: 'absolute', opacity: outroOpacity, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <h1 style={{ color: '#2a9d8f', fontSize: '70px', fontWeight: 'bold', fontFamily: 'sans-serif' }}>
            Puzzle Solved!
          </h1>
          <h2 style={{ color: 'white', fontSize: '40px', fontWeight: 'normal', fontFamily: 'sans-serif', marginTop: '30px' }}>
            Follow @LearnChess.live for more daily chess puzzles.
          </h2>
        </div>
      </AbsoluteFill>

      {/* Main Board Container */}
      <AbsoluteFill style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${boardScale})` }}>
        <div style={{ position: 'relative', width: boardWidth, height: boardWidth, boxShadow: '0 0 50px rgba(0,0,0,0.5)', borderRadius: '12px', overflow: 'hidden' }}>
          <Chessboard 
            position={currentFen} 
            boardWidth={boardWidth}
            animationDuration={0} // MUST be 0, otherwise react-chessboard crashes Remotion headless browser
            boardOrientation={isBlackBottom ? 'black' : 'white'}
            customDarkSquareStyle={{ backgroundColor: '#3d3d3d' }}
            customLightSquareStyle={{ backgroundColor: '#7a7a7a' }}
            customNotationStyle={{ color: 'rgba(0,0,0,0.45)', fontWeight: 700, fontSize: 11 }}
            customSquareStyles={customSquareStyles}
            customPieces={customPieces}
          />
          
          {/* Custom Overlay for Animating Piece */}
          {animatingMove && animatingMove.move && animatingMove.piece && (
            <AbsoluteFill>
              <Img 
                src={staticFile(`assets/pieces/${animatingMove.piece.color}${animatingMove.piece.type.toUpperCase()}.svg`)}
                style={{
                  position: 'absolute',
                  width: squareSize,
                  height: squareSize,
                  left: interpolate(frame, [animStartFrame, animStartFrame + animFrames], [getSquarePos(animatingMove.move.from).x, getSquarePos(animatingMove.move.to).x]),
                  top: interpolate(frame, [animStartFrame, animStartFrame + animFrames], [getSquarePos(animatingMove.move.from).y, getSquarePos(animatingMove.move.to).y]),
                  zIndex: 100 // ensure it draws over other pieces
                }}
              />
            </AbsoluteFill>
          )}
        </div>
      </AbsoluteFill>

      {/* Audio Setup */}
      {/* Intro Voice */}
      <Sequence from={0} durationInFrames={hookDuration}>
        <Audio src={staticFile("Chess_Project_Voices/canyoufind.wav")} volume={1.0} />
      </Sequence>

      {/* Brilliant Voice for Reveal */}
      <Sequence from={hookDuration + thinkDuration} durationInFrames={revealDuration}>
        <Audio src={staticFile("Chess_Project_Voices/Brilliant.mp3")} volume={1.0} />
      </Sequence>

      {/* Outro Voice */}
      <Sequence from={scene5Start + 15}>
        <Audio src={staticFile("Chess_Project_Voices/win.mp3")} volume={0.8} />
      </Sequence>

      {/* Chess Piece Movement Sounds */}
      {moveTimings.map((startFrame, index) => (
        <Sequence key={index} from={Math.floor(startFrame + animFrames)} layout="none">
          <Audio src={staticFile("assets/sounds/move.mp3")} volume={1.0} />
        </Sequence>
      ))}

    </AbsoluteFill>
  );
};
