# Ollama Sniffer

Transparent debug proxy between any LLM client and Ollama. Logs full request/response payloads without modifying traffic.

## Why

When debugging tool calling, prompt formatting, or unexpected model behavior, you need to see the exact JSON going to and from Ollama. This proxy sits in between, logs everything, and forwards untouched.

## Usage

```bash
python3 sniffer.py
```

Then point your client to `http://127.0.0.1:11435` instead of `:11434`.

## What gets logged

Only chat/completion endpoints are captured:
- `/v1/chat/completions`
- `/api/chat`
- `/api/generate`

Other endpoints (model list, health, etc.) are forwarded silently.

## Log output

Logs go to `/tmp/ollama-sniff/`:

```
/tmp/ollama-sniff/
├── _summary.log          # One-line per request: model, stream, tools, message count
├── req-0001-143022-456.json   # Full request body
├── resp-0001-143022-456.txt   # Full response body
└── ...
```

## Configuration

Edit the constants at the top of `sniffer.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Upstream Ollama address |
| `LISTEN_PORT` | `11435` | Port to listen on |
| `LOG_DIR` | `/tmp/ollama-sniff` | Where to write logs |

## Dependencies

Python 3 standard library only. No pip install needed.
