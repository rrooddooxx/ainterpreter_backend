from whisper_live.client import TranscriptionClient

print("CLIENTE #2")

client = TranscriptionClient(
  "localhost",
  9091,
  lang="es",
  translate=False,
  model="tiny",
  use_vad=False,
  save_output_recording=False
)

client(rtsp_url="rtsp://localhost:8888/test")
