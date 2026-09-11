from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_PATH = "yolov8n.pt"

# Classes du dataset COCO correspondant aux véhicules
VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

LINE_Y_RATIO = 0.5  # position de la ligne de comptage (0.5 = au milieu de la vidéo)