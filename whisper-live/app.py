from whisper_live.client import TranscriptionClient

client = TranscriptionClient(
  "localhost",
  9090,
  lang="es",
  translate=False,
  model="tiny",
  use_vad=True,
  save_output_recording=False,                         # Only used for microphone input, False by Default
  output_recording_filename="./output_recording.wav"  # Only used for microphone input
)

client(rtsp_url="rtsp://localhost:8554/test")
