# Resource Intake API

Two entry paths to `/api/process_message/`:

1) **JSON** (text):
```bash
curl -X POST http://localhost:8000/api/process_message/ \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "I have a few generators and three dozen water bottles available; I am near Kilpisjärvi K-Market.",
    "metadata": {
      "phone_number": "+35843958435",
      "user_type": "civilian"
    }
  }'
````

2. **Multipart** (audio):

```bash
curl -X POST http://localhost:8000/api/process_message/ \
  -F metadata='{"phone_number":"+35843958435","user_type":"civilian"}' \
  -F file=@sample.wav
```

### Configure the LLM backend

The app reads a single row from `app_settings`:

* `llm_backend`: `openai` or `hf`
* `openai_model`: e.g. `gpt-4o-mini`
* `hf_model_id`: default `microsoft/Phi-3.5-MoE-instruct` (multilingual, good English + Finnish)
* `hf_device`: `cpu` | `auto`

Create or modify via SQLite shell:

```sql
INSERT INTO app_settings (llm_backend, openai_model, hf_model_id, hf_device)
VALUES ('hf', 'gpt-4o-mini', 'microsoft/Phi-3.5-MoE-instruct', 'auto');
```

### Notes

* If a precise GeoJSON is not provided in metadata, the server attempts geocoding of the extracted `location_text` using OpenStreetMap Nominatim.
* Audio transcription uses local **faster-whisper**. For Finnish, `medium` yields strong accuracy. Use `WHISPER_DEVICE=cuda` if a GPU is available.
