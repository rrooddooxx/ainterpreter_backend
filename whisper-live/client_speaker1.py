from whisper_live.client import TranscriptionClient

print("CLIENTE #1")

client = TranscriptionClient(
  "localhost",
  9090,
  lang="es",
  translate=False,
  model="small",
  use_vad=False,
  save_output_recording=False,                         
)

client(rtsp_url="rtsp://localhost:8554/test")
