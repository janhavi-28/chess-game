import assetsData from '../public/metadata/assets.json';

export function getAssetsForEvent(classification: string) {
  const c = classification.toLowerCase();
  
  // Find matching sounds based on tags
  const matchingSounds = assetsData.sounds.filter(s => 
    s.tags.some(t => c.includes(t) || t.includes(c))
  );
  
  // Find matching memes based on tags
  const matchingMemes = assetsData.memes.filter(m => 
    m.tags.some(t => c.includes(t) || t.includes(c))
  );

  let audioFile = matchingSounds.length > 0 
    ? matchingSounds[Math.floor(Math.random() * matchingSounds.length)].file 
    : null;
    
  let memeFile = matchingMemes.length > 0 
    ? matchingMemes[Math.floor(Math.random() * matchingMemes.length)].file 
    : null;

  // Fallbacks for positive moves (since 'best' isn't explicitly tagged yet)
  if (!audioFile) {
    if (c.includes('best') || c.includes('brilliant') || c.includes('good') || c.includes('excellent') || c.includes('book')) {
      audioFile = assetsData.sounds.find(s => s.id === 'sfx_good_move')?.file || null;
    }
  }
  
  // Fallback for end of puzzle (often a win)
  if (c.includes('mate') || c.includes('win')) {
    audioFile = assetsData.sounds.find(s => s.id === 'sfx_win')?.file || null;
  }

  return { audioFile, memeFile };
}
