# tracking_service.py
import cv2
import os
import json

def initialize_tracker(tracker_type="CSRT"):
    tracker_type = tracker_type.upper()
    if tracker_type == "CSRT":
        return cv2.TrackerCSRT_create()
    elif tracker_type == "KCF":
        return cv2.TrackerKCF_create()
    else:
        raise ValueError(f"Tracker non supporté : {tracker_type}")

def track_objects_in_scene(frames_dir, annotations, tracker_type="CSRT"):
    frame_files = sorted([
        f for f in os.listdir(frames_dir)
        if f.endswith(".jpg") or f.endswith(".png")
    ])

    if not frame_files:
        raise ValueError("Aucune image trouvée dans le dossier de frames.")

    # Charger la première image
    first_frame_path = os.path.join(frames_dir, frame_files[0])
    frame = cv2.imread(first_frame_path)
    if frame is None:
        raise ValueError(f"Impossible de lire la première frame : {first_frame_path}")

    trackers = []
    object_ids = []

    for obj in annotations.get("objects", []):
        bbox = tuple(obj["bbox"])  # [x, y, w, h]
        tracker = initialize_tracker(tracker_type)
        tracker.init(frame, bbox)
        trackers.append(tracker)
        object_ids.append(obj["id"])

    tracking_data = {obj_id: [{"frame": 0, "bbox": annotations["objects"][i]["bbox"]}]
                     for i, obj_id in enumerate(object_ids)}

    # Parcourir les frames suivantes
    for idx, filename in enumerate(frame_files[1:], start=1):
        frame_path = os.path.join(frames_dir, filename)
        frame = cv2.imread(frame_path)
        if frame is None:
            continue

        for i, tracker in enumerate(trackers):
            success, bbox = tracker.update(frame)
            if success:
                x, y, w, h = [int(v) for v in bbox]
                tracking_data[object_ids[i]].append({"frame": idx, "bbox": [x, y, w, h]})

    return tracking_data
