# video_utils.py
import cv2
import requests
import os

def extract_frames_from_video(video_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_filename = os.path.join(output_dir, f"frame_{frame_idx:04d}.jpg")
        cv2.imwrite(frame_filename, frame)
        frame_idx += 1

    cap.release()
    return frame_idx

def save_video_from_frames(frames_dir, output_path, fps=1):
    frame_files = sorted([
        f for f in os.listdir(frames_dir)
        if f.endswith(".jpg") or f.endswith(".png")
    ])

    if not frame_files:
        raise ValueError("Aucune image trouvée dans le dossier de frames.")

    first_frame_path = os.path.join(frames_dir, frame_files[0])
    first_frame = cv2.imread(first_frame_path)
    height, width, _ = first_frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for filename in frame_files:
        frame = cv2.imread(os.path.join(frames_dir, filename))
        if frame is not None:
            out.write(frame)

    out.release()
    return output_path

def call_scene_splitter(video_path, scene_api_url, threshold=0.6):
    files = {'video_file': open(video_path, 'rb')}
    data = {'threshold': threshold}

    try:
        response = requests.post(scene_api_url, files=files, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}