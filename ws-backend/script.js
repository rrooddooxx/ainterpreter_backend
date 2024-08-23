import { io } from 'socket.io-client';

const socket = io('http://localhost:3000');

// Enviar un mensaje al servidor
socket.emit('transcription', 'Hola desde el cliente');

// Escuchar cuando el servidor se desconecta
socket.on('disconnect', () => {
  console.log('Servidor desconectado');
});