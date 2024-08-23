import express from 'express';
import http from 'http';
import { Server } from 'socket.io';

const app = express();
const server = http.createServer(app);
const io = new Server(server);

// Ruta principal
app.get('/', (req, res) => {
  res.send('Servidor de WebSockets con Socket.io está en funcionamiento');
});

// WebSocket connection
io.on('connection', (socket) => {
  console.log('Client connected.');

  // Recibir mensaje del cliente
  socket.on('transcription', (data) => {
    console.log('Transcription:', data);
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected.');
  });
});

const PORT = 3000;
server.listen(PORT, () => {
  console.log(`Servidor escuchando en http://localhost:${PORT}`);
});
