<<<<<<< HEAD
# Kidney Disease Detection using Deep Learning

A production-ready AI medical web application for kidney CT image classification with FastAPI, PostgreSQL, PyTorch, Grad-CAM explainability, and a polished vanilla HTML/CSS/JavaScript frontend.

## Features

- Single-page home prediction flow that resets on refresh
- PostgreSQL storage for users and prediction history
- ResNet34/PyTorch inference with model loaded once at startup
- Grad-CAM heatmap generated for every prediction
- History search by name or phone with pagination
- Sample CT image download catalog and ZIP download endpoint
- Dark/light mode, drag and drop upload, image preview, progress bars, toasts
- Render-ready backend and Vercel-ready frontend

## Project Structure

```text
backend/
  app/
    api/routers/
    database/
    models/
    schemas/
    services/
    utils/
    uploads/
    main.py
  alembic/
frontend/
  assets/
  css/
  js/
  sample-images/
```

## Model Setup

Place your existing model file here:

```text
backend/model/gradcam_resnet34_full.pth
```

You can also set `MODEL_PATH` in the environment if the model lives elsewhere.

The classifier classes are:

- Normal
- Kidney Stone
- Kidney Cyst
- Kidney Tumor

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

The API and frontend will be served at:

```text
http://127.0.0.1:8000
```

## PostgreSQL

Create a database, then update `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/kidney_ai
```

Run migrations:

```bash
cd backend
alembic upgrade head
```

## Sample Images

Put sample CT scans into:

```text
frontend/sample-images/normal/
frontend/sample-images/stone/
frontend/sample-images/tumor/
frontend/sample-images/cyst/
```

The app automatically lists downloadable sample files from these folders.

## API Endpoints

- `POST /api/user`
- `POST /api/predict`
- `GET /api/history`
- `GET /api/sample-images`
- `GET /api/sample-images/download-all`
- `GET /health`

## Render Deployment

Recommended production setup:

- Backend: Render Web Service
- Database: Render PostgreSQL, Neon, or Supabase PostgreSQL
- Frontend: Vercel static project

This split is the cleanest portfolio/hackathon hosting setup: the FastAPI service handles PyTorch inference and database writes, while Vercel serves the frontend quickly.

Simpler all-in-one setup:

- Deploy only the backend on Render.
- FastAPI will also serve the `frontend/` files from `/`.
- This is easier for demos because there is only one public URL.

1. Create a PostgreSQL database on Render.
2. Create a Web Service from this repository.
3. Set root directory to `backend`.
4. Build command:

```bash
pip install -r requirements.txt
```

5. Start command:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

6. Add environment variables from `.env.example`, including `DATABASE_URL`, `MODEL_PATH`, and `ALLOWED_ORIGINS`.
7. Upload or mount `gradcam_resnet34_full.pth` at the configured `MODEL_PATH`.

## Vercel Deployment

The frontend is static and can be deployed from the `frontend` directory.

Set this environment variable in Vercel:

```text
API_BASE_URL=https://your-render-backend.onrender.com
```

If deploying as static files only, update `frontend/js/config.js` with your backend URL before deployment.

Example:

```js
window.KIDNEY_AI_CONFIG = {
  API_BASE_URL: "https://your-render-backend.onrender.com"
};
```

## Sample Image Catalog

The website includes sample image folders and category ZIP downloads:

```text
frontend/sample-images/
  archives/
    Cyst.zip
    Stone.zip
    Tumor.zip
  cyst/
  stone/
  tumor/
  normal/
```

The Sample Images page shows real preview images when files are present. Users can download a single CT image and drag it into the analyzer to test the model, or download a whole category ZIP.

## Medical Disclaimer

This application is for educational and research support only. It is not a medical device and must not replace diagnosis, treatment, or advice from qualified healthcare professionals.
=======
# Null_pointers_Renal
>>>>>>> 8fc84a8171837d9110eb114cb849d9177de81de5
