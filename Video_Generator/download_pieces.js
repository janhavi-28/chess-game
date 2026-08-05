const fs = require('fs');
const https = require('https');
const path = require('path');
const pieces = ['wP', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bP', 'bN', 'bB', 'bR', 'bQ', 'bK'];
const destDir = path.join(__dirname, 'public', 'assets', 'pieces');
if (!fs.existsSync(destDir)) { fs.mkdirSync(destDir, { recursive: true }); }
pieces.forEach(p => {
  const url = `https://raw.githubusercontent.com/lichess-org/lila/master/public/piece/cburnett/${p}.svg`;
  const file = fs.createWriteStream(path.join(destDir, `${p}.svg`));
  https.get(url, response => {
    response.pipe(file);
    file.on('finish', () => file.close());
  });
});
