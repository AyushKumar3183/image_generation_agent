# Image Generation Agent

Fashion-focused image generation service built with **Google ADK**, **FastAPI**, **Gemini**, and **AWS S3**.

Generate studio-quality fashion images from text prompts, with optional reference images, parallel multi-image output, and automatic S3 upload.

## Features

- **Single agent architecture** — one ADK `root_agent` routes all requests
- **Unified flow** — `Agent → Tool → Service` for both chat and HTTP API
- **Auto workflow detection** from `reference_images` count:
  - `0` → text-to-image
  - `1` → image-to-image
  - `2+` → multi-image generation
- **1–4 images per request** with parallel Gemini calls and parallel S3 uploads
- **Prompt-driven quality rules** — studio composition, fashion quality, and multi-image variation (no hardcoded prompts in service code)
- **S3 storage** — images uploaded to S3; API returns public URLs

## Architecture

```
User / API
    ↓
agent.py (root_agent)
    ↓
generate_image_tool.py
    ↓
image_generation_service.py
    ↓
Gemini (gemini-3.1-flash-image) + AWS S3
```

| Entry point | Command | Use case |
|-------------|---------|----------|
| ADK chat UI | `adk web` | Interactive agent chat |
| HTTP API | `uvicorn main:app --reload` | REST API + Swagger docs |

Both paths use the same agent and tool — no duplicate business logic.

## Project structure

```
image_generation_agent/
├── agent.py                 # ADK root agent
├── agent_runner.py          # Runs agent from HTTP API
├── api/                     # FastAPI routes & schemas
├── tools/
│   └── generate_image_tool.py
├── services/
│   ├── image_generation_service.py
│   ├── gemini_image_backend.py
│   └── s3_storage_service.py
├── prompts/
│   ├── image_generation_agent_prompt.py   # Agent instructions
│   ├── studio_composition_rules.py        # Front-facing studio format
│   ├── fashion_quality_rules.py           # Background, face, outfit rules
│   └── multi_image_variation_rules.py     # Distinct variations per image
├── models/
└── utils/
main.py                      # Uvicorn entry point
requirements.txt
.env.example
```

## Setup

### 1. Clone and install

```bash
cd "image genertion agent"
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Google AI / Gemini API key |
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_REGION` | S3 region (e.g. `ap-south-1`) |
| `AWS_S3_BUCKET_NAME` | Target S3 bucket |
| `S3_KEY_PREFIX` | Folder prefix (default: `generated-images`) |
| `LOG_LEVEL` | Optional — `WARNING` (default) or `INFO` |

## Run

### ADK web chat

From the project root (where `image_generation_agent/` lives):

```bash
adk web
```

### HTTP API

```bash
uvicorn main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## API

### `POST /v1/images/generate`

**Request body:**

```json
{
  "prompt": "Generate a luxury evening gown",
  "reference_images": [],
  "resolution": "1K",
  "number_of_images": 1
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `prompt` | string | required | Creative instruction (passed verbatim to the model) |
| `reference_images` | string[] | `[]` | Optional HTTP/HTTPS image URLs |
| `resolution` | `"1K"` \| `"2K"` \| `"4K"` | `"1K"` | Output resolution |
| `number_of_images` | int (1–4) | `1` | How many images to generate |

**Success response:**

```json
{
  "status": "success",
  "image_urls": [
    "https://your-bucket.s3.region.amazonaws.com/generated-images/uuid-1.jpg"
  ],
  "mime_type": "image/jpeg",
  "resolution": "1K",
  "workflow": "text_to_image",
  "reference_image_count": 0,
  "number_of_images": 1,
  "request_id": "uuid",
  "model": "gemini-3.1-flash-image"
}
```

### Examples

**Text-to-image (4 variations):**

```json
{
  "prompt": "Royal blue silk saree with gold embroidery",
  "reference_images": [],
  "resolution": "1K",
  "number_of_images": 4
}
```

**Image-to-image:**

```json
{
  "prompt": "Make this dress black",
  "reference_images": ["https://cdn.example.com/dress.jpg"],
  "resolution": "1K",
  "number_of_images": 1
}
```

## Customizing prompts

All generation rules live in `image_generation_agent/prompts/`. Edit these files to change behavior without touching service code:

| File | Purpose |
|------|---------|
| `studio_composition_rules.py` | Front-facing, full-length, centered studio format |
| `fashion_quality_rules.py` | Clean background, face visibility, outfit details |
| `multi_image_variation_rules.py` | How each image in a batch differs (same format, different styling) |
| `image_generation_agent_prompt.py` | ADK agent routing instructions |

`utils/prompt_builder.py` assembles these automatically for every Gemini call.

## Models

| Component | Model |
|-----------|-------|
| ADK agent (routing) | `gemini-2.5-flash` |
| Image generation | `gemini-3.1-flash-image` |

Image model is configured in `image_generation_agent/utils/config.py`.

## Security

- Never commit `.env` — it is listed in `.gitignore`
- Rotate API keys if they are ever exposed
- Use `.env.example` as a template only

## License

Private project — add your license here if needed.
