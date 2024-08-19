ffmpeg -re -stream_loop -1 -i /Users/sebastiankravetz/Dev/Projects/AInterpreter_Hackathon/backend/WhisperLiveServer/scripts/calila.mp4 -c copy -f rtsp rtsp://localhost:8554/test


http://192.168.3.34:8080