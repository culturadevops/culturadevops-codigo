// La MISMA app de notas, en Electron: la comparación justa del vídeo.
const { app, BrowserWindow } = require('electron');

app.whenReady().then(() => {
  const v = new BrowserWindow({ width: 420, height: 380 });
  v.loadFile('index.html');
});
app.on('window-all-closed', () => app.quit());
