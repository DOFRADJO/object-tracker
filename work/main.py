from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil
import uuid
import json
import requests

from video_utils import extract_frames_from_video, save_video_from_frames
from tracking_service import track_objects_in_scene
from db import save_tracking_data, get_tracking_data

app = FastAPI(title="Microservice de tracking d'objet")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Répertoires
UPLOAD_DIR = "videos"
FRAMES_ROOT_DIR = "frames"
RESULTS_DIR = "results"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FRAMES_ROOT_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Servir l'interface + vidéos générées
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    # Génère un ID unique
    video_id = str(uuid.uuid4())
    filename = f"{video_id}_{file.filename}"
    video_path = os.path.join(UPLOAD_DIR, filename)

    # Enregistre la vidéo localement
    with open(video_path, "wb") as f_out:
        shutil.copyfileobj(file.file, f_out)

    # Appelle le microservice de découpage
    try:
        scene_api_url = "http://127.0.0.8:8001/split_scene"
        with open(video_path, "rb") as f_video:
            files = {'video_file': (filename, f_video, 'video/mp4')}
            data = {'threshold': '0.5'}
            response = requests.post(scene_api_url, files=files, data=data)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Échec du découpage vidéo")

        scenes = response.json()
        return {
            "video_id": video_id,
            "video_path": video_path,
            "scenes": scenes
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur appel découpage: {str(e)}")

@app.post("/track")
async def track_objects(
    video_id: str = Form(...),
    annotations_json: str = Form(...),
    tracker_type: str = Form("CSRT")
):
    annotations = json.loads(annotations_json)

    # Recherche du fichier vidéo par ID
    video_file = next((f for f in os.listdir(UPLOAD_DIR) if f.startswith(video_id)), None)
    if not video_file:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")

    video_path = os.path.join(UPLOAD_DIR, video_file)
    frames_dir = os.path.join(FRAMES_ROOT_DIR, video_id)
    os.makedirs(frames_dir, exist_ok=True)

    # Extraction des frames
    extract_frames_from_video(video_path, frames_dir)

    # Tracking
    tracking_data = track_objects_in_scene(frames_dir, annotations, tracker_type)

    # Enregistrement
    save_tracking_data(video_id, tracking_data)

    # Vidéo finale à 1 FPS
    output_video_path = os.path.join(RESULTS_DIR, f"{video_id}.mp4")
    save_video_from_frames(frames_dir, output_video_path, fps=1)

    return {
        "video_id": video_id,
        "tracking_data": tracking_data,
        "video_result_url": f"/results/{video_id}.mp4"
    }

@app.get("/tracking")
def get_tracking(video_id: str):
    data = get_tracking_data(video_id)
    if not data:
        raise HTTPException(status_code=404, detail="Aucune donnée trouvée")
    return data
