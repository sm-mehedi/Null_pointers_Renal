# Kidney Disease Detection using Deep Learning

A no-database AI medical demo for kidney CT image classification. The app uses a FastAPI backend, a PyTorch ResNet34 model, Grad-CAM explainability, and a vanilla HTML/CSS/JavaScript frontend.

## Features

- Patient name and phone input for the current session only
- Drag-and-drop or browse upload for JPG/PNG CT images
- ResNet34/PyTorch inference loaded once at backend startup
- Disease prediction, confidence score, and class probabilities
- Grad-CAM heatmap generated for every prediction
- Brief disease explanation on the result page
- PDF report download with patient info, prediction, probabilities, original CT, and heatmap
- Sample CT image catalog with individual image downloads and ZIP downloads
- No database, no login, no history storage; refreshing starts a new session

## Project Structure

```text
backend/
  app/
    api/routers/
    core/
    services/
    utils/
    main.py
  model/
    gradcam_resnet34_full.pth
frontend/
  assets/
  css/
  js/
  sample-images/
```

## Model Setup

The model file should be available at:

```text
backend/model/gradcam_resnet34_full.pth
```

The classifier classes are:

- Kidney Cyst
- Normal
- Kidney Stone
- Kidney Tumor

## Local Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Environment Variables

```env
APP_NAME=Kidney Disease Detection using Deep Learning
ENVIRONMENT=production
MODEL_PATH=model/gradcam_resnet34_full.pth
ALLOWED_ORIGINS=https://your-render-app.onrender.com
MAX_UPLOAD_MB=10
```

No `DATABASE_URL` is required.

## API Endpoints

- `POST /api/predict`
- `POST /api/report-pdf`
- `GET /api/sample-images`
- `GET /api/sample-images/download-all`
- `GET /health`

## Render Deployment

Create a Render Web Service from this repository.

Recommended settings:

```text
Root directory: backend
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```env
ENVIRONMENT=production
MODEL_PATH=model/gradcam_resnet34_full.pth
ALLOWED_ORIGINS=https://your-render-app.onrender.com
MAX_UPLOAD_MB=10
```

FastAPI serves the frontend from `/`, so one Render service is enough for the demo.

## Medical Disclaimer

This application is for educational and research support only. It is not a medical device and must not replace diagnosis, treatment, or advice from qualified healthcare professionals.
