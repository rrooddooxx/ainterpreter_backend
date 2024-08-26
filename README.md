# HeyAru Backend
> Entorno Backend para proyecto "HeyAru"
> AIHackathon 2024. Equipo #311

## Servidor Live Whisper + Servidor RTSP

En un archivo Docker Compose (docker-compose.yml) se han definido dos servicios,
uno despliega el contenedor de Whisper Live, 
y el otro despliega una imagen de un servidor RTSP con MediaMTX

- Ejecución:
  - `cd whisper-live/`
  - `docker compose up`
- Requisitos:
  - Contar con Docker Desktop instalado


## Servidor AioRTC
- Ejecución
  - `python -m venv venv`
  - `source venv/bin/activate`
  - `pip install -r requirements.txt`
  - `python3 server.py`
  - Visitar en el navegador: `localhost:8080`
  - El servidor RTSP ya debe estar corriendo (va adosado al whisper-live)
