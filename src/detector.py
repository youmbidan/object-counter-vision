import cv2
from ultralytics import YOLO

from src.config import MODEL_PATH, VEHICLE_CLASSES, LINE_Y_RATIO

model = YOLO(MODEL_PATH)


def process_video(video_path: str, output_path: str, line_y_ratio: float = LINE_Y_RATIO):
    """Fonction qui traite une vidéo : suit les véhicules, compte ceux qui franchissent une ligne horizontale,
    par direction (montant/descendant) et par catégorie. Retourne les comptages et le chemin
    de la vidéo annotée."""
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    cap.release()

    line_y = int(height * line_y_ratio)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    track_history = {}   # track_id -> dernière position y du centre
    crossed_ids = set()  # track_id déjà comptés, pour ne jamais compter deux fois
    counts = {"down": {}, "up": {}}  # comptage par catégorie et par direction

    results_stream = model.track(
        source=video_path,
        persist=True,
        classes=list(VEHICLE_CLASSES.keys()),
        stream=True,
        verbose=False,
    )

    for result in results_stream:
        frame = result.orig_img.copy()

        if result.boxes.id is not None:
            for box, track_id, cls_id in zip(
                result.boxes.xyxy.cpu().numpy(),
                result.boxes.id.cpu().numpy(),
                result.boxes.cls.cpu().numpy(),
            ):
                track_id = int(track_id)
                class_name = VEHICLE_CLASSES.get(int(cls_id), "vehicle")
                x1, y1, x2, y2 = box
                cy = int((y1 + y2) / 2)

                previous_y = track_history.get(track_id)
                if previous_y is not None and track_id not in crossed_ids:
                    if previous_y < line_y <= cy:
                        counts["down"][class_name] = counts["down"].get(class_name, 0) + 1
                        crossed_ids.add(track_id)
                    elif previous_y > line_y >= cy:
                        counts["up"][class_name] = counts["up"].get(class_name, 0) + 1
                        crossed_ids.add(track_id)

                track_history[track_id] = cy

        annotated = result.plot()
        cv2.line(annotated, (0, line_y), (width, line_y), (0, 0, 255), 2)
        writer.write(annotated)

    writer.release()
    return counts, output_path

def get_preview_frame(video_path: str, line_y_ratio: float):
    """Extrait la première frame de la vidéo avec la ligne de comptage dessinée, pour prévisualisation."""
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None

    height, width = frame.shape[:2]
    line_y = int(height * line_y_ratio)
    cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 3)

    return frame[..., ::-1]  # BGR -> RGB pour l'affichage