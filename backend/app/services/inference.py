import base64
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from fastapi import HTTPException
from PIL import Image
from torchvision import models, transforms

from app.core.config import settings

CLASSES = ["Kidney Cyst", "Normal", "Kidney Stone", "Kidney Tumor"]
MODEL_NAME = "ResNet34 Grad-CAM"


@dataclass
class PredictionResult:
    prediction: str
    confidence: float
    probabilities: dict[str, float]
    original_image: str
    heatmap_image: str
    model_name: str = MODEL_NAME


class GradCAM:
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.activations = None
        self.gradients = None
        self.forward_handle = target_layer.register_forward_hook(self._save_activation)
        self.backward_handle = target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, _module, _inputs, output):
        self.activations = output.detach()

    def _save_gradient(self, _module, _grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate(self, tensor: torch.Tensor, class_index: int) -> np.ndarray:
        self.model.zero_grad(set_to_none=True)
        output = self.model(tensor)
        score = output[:, class_index].sum()
        score.backward(retain_graph=True)

        if self.activations is None or self.gradients is None:
            raise HTTPException(status_code=500, detail="Grad-CAM hooks did not capture model features.")

        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = (weights * self.activations).sum(dim=1).squeeze()
        cam = torch.relu(cam)
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)
        return cam.cpu().numpy()


class ModelService:
    def __init__(self):
        self.model: nn.Module | None = None
        self.gradcam: GradCAM | None = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def load(self):
        if self.model is not None:
            return

        model_path = settings.resolved_model_path
        if not model_path.exists():
            raise RuntimeError(f"Model file not found at {model_path}")

        checkpoint = torch.load(model_path, map_location=self.device)
        model = self._build_model_from_checkpoint(checkpoint)
        model.to(self.device)
        model.eval()

        target_layer = self._find_last_conv(model)
        self.model = model
        self.gradcam = GradCAM(model, target_layer)

    def _build_model_from_checkpoint(self, checkpoint: Any) -> nn.Module:
        if isinstance(checkpoint, nn.Module):
            return checkpoint

        state_dict = checkpoint.get("model_state_dict", checkpoint.get("state_dict", checkpoint)) if isinstance(checkpoint, dict) else checkpoint
        model = models.resnet34(weights=None)
        model.fc = nn.Linear(model.fc.in_features, len(CLASSES))

        cleaned_state = {}
        for key, value in state_dict.items():
            cleaned_key = key.replace("module.", "")
            cleaned_state[cleaned_key] = value
        model.load_state_dict(cleaned_state, strict=False)
        return model

    def _find_last_conv(self, model: nn.Module) -> nn.Module:
        last_conv = None
        for module in model.modules():
            if isinstance(module, nn.Conv2d):
                last_conv = module
        if last_conv is None:
            raise RuntimeError("No convolution layer found for Grad-CAM.")
        return last_conv

    def predict(self, image_bytes: bytes) -> PredictionResult:
        if self.model is None or self.gradcam is None:
            raise HTTPException(status_code=503, detail="Model is not loaded.")

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Could not read the uploaded image.") from exc

        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze().cpu().numpy()

        class_index = int(np.argmax(probs))
        cam = self.gradcam.generate(tensor, class_index)

        prediction = CLASSES[class_index]
        confidence = float(probs[class_index] * 100)
        probabilities = {label: float(prob * 100) for label, prob in zip(CLASSES, probs)}

        return PredictionResult(
            prediction=prediction,
            confidence=confidence,
            probabilities=probabilities,
            original_image=self._image_to_data_url(image),
            heatmap_image=self._heatmap_to_data_url(image, cam),
        )

    def _image_to_data_url(self, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    def _heatmap_to_data_url(self, image: Image.Image, cam: np.ndarray) -> str:
        cam_image = Image.fromarray(np.uint8(cam * 255)).resize(image.size, Image.Resampling.BILINEAR)
        heat = np.array(cam_image)
        color = np.zeros((heat.shape[0], heat.shape[1], 3), dtype=np.uint8)
        color[..., 0] = heat
        color[..., 1] = np.clip(255 - np.abs(heat.astype(int) - 128) * 2, 0, 255)
        color[..., 2] = 255 - heat

        original = np.array(image).astype(np.float32)
        overlay = (0.58 * original + 0.42 * color).clip(0, 255).astype(np.uint8)
        return self._image_to_data_url(Image.fromarray(overlay))


model_service = ModelService()
