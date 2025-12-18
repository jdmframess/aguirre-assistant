# Aguirre – Asistente Virtual AEAT

Monorepo con un frontend en Next.js, un backend en FastAPI con RAG ligero y un pipeline de ingestión.

## Estructura

- `frontend/`: aplicación Next.js con interfaz básica para preguntar al asistente.
- `backend/`: API FastAPI con endpoint `/chat` que usa RAG sobre un índice vectorial local.
- `ingestion/`: pipeline para convertir documentos en `data/raw/` a chunks en `data/processed/` y construir el índice vectorial.
- `common/`: utilidades compartidas (p.ej. embedding hashed).
- `data/`: directorio compartido para documentos de entrada y salida.

Endpoints clave del backend:
- `GET /health`: comprobación de estado.
- `POST /chat`: recibe `question` y devuelve `answer` + `citations`.

## Requisitos

- Docker y Docker Compose.
- Opcional: Node.js 20+ y Python 3.11+ si quieres ejecutar fuera de contenedores.

## Puesta en marcha con Docker Compose

```bash
docker compose up --build
```

Servicios expuestos:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

El frontend utiliza la variable `NEXT_PUBLIC_BACKEND_URL` y en el entorno de Docker Compose ya apunta a `http://backend:8000`.

## Ingestión de documentos y construcción del índice

1. Añade archivos `.txt` o `.md` en `data/raw/`.
2. Ejecuta el pipeline para generar chunks y el índice vectorial (usando `make` o Docker Compose):

```bash
make ingest
# o con Docker Compose
docker compose run --rm --profile ingestion ingestion
```

Los resultados se guardan en `data/processed/` como JSON con chunks y metadatos (`source`, `url`, `date`, `title`) y en `data/processed/vector_index.json` con los embeddings.

## Flujo del endpoint `/chat`

1. Se genera un embedding hashed de la pregunta.
2. Se buscan los `topK` (3 por defecto) fragmentos más similares en `data/processed/vector_index.json`.
3. Se construye una respuesta simple concatenando los fragmentos relevantes.
4. Se devuelven `answer` y `citations` (cada cita incluye `url`, `title`, `retrieved_at`).

## Desarrollo local sin Docker

- Backend:
  ```bash
  cd backend
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  uvicorn main:app --reload --port 8000
  ```

- Frontend:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```

- Pipeline de ingestión + índice vectorial:
  ```bash
  make ingest
  ```
