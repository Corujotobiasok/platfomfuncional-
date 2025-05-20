const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let flaskProcess = null;
const FLASK_PORT = 5000;

function createWindow() {
  const win = new BrowserWindow({
    width: 1000,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
    }
  });

  win.loadURL(`http://localhost:${FLASK_PORT}`);
}

function startFlask() {
  const scriptPath = path.join(__dirname, 'app', 'app.py');
  flaskProcess = spawn('python', [scriptPath]);

  flaskProcess.stdout.on('data', (data) => {
    console.log(`Flask: ${data}`);
  });

  flaskProcess.stderr.on('data', (data) => {
    console.error(`Flask error: ${data}`);
  });
}

app.whenReady().then(() => {
  startFlask();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('before-quit', () => {
  if (flaskProcess) flaskProcess.kill();
});
