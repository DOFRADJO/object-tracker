import cv2
import numpy as np
from rembg import remove
from PIL import Image

# Variables globales
selected_contour = None
frame = None
cap = None

def select_object(event, x, y, flags, param):
    global selected_contour
    if event == cv2.EVENT_LBUTTONDOWN:
        for contour in contours:
            if cv2.pointPolygonTest(contour, (x, y), True) >= 0:
                selected_contour = contour
                cv2.drawContours(frame, [contour], -1, (255, 0, 0), 2)  # Contour en rouge
                cv2.imshow("Sélection d'objet", frame)
                break

# Charger la vidéo
cap = cv2.VideoCapture('test_tracking.wmv')  # Remplacez avec le chemin de votre vidéo

# Lire la première image
ret, frame = cap.read()
if not ret:
    print("Erreur lors de la lecture de la vidéo.")
    cap.release()
    exit()

# Appliquer rembg pour retirer l'arrière-plan
pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
output_image = remove(pil_image)

# Convertir l'image de sortie en format OpenCV
output_image_cv = cv2.cvtColor(np.array(output_image), cv2.COLOR_RGBA2BGR)

# Convertir l'image en niveaux de gris et détecter les contours
gray = cv2.cvtColor(output_image_cv, cv2.COLOR_BGR2GRAY)
_, thresholded = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

# Trouver les contours
contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Afficher les contours détectés
for contour in contours:
    cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)  # Contours en vert

# Afficher l'image avec les contours
cv2.imshow("Sélectionnez l'objet", frame)

# Configurer le callback pour la sélection par clic
cv2.setMouseCallback("Sélectionnez l'objet", select_object)

# Attendre que l'utilisateur sélectionne un objet
while True:
    if selected_contour is not None:
        break
    if cv2.waitKey(1) & 0xFF == 27:  # Échap pour quitter
        break

# Vérifiez si un objet a été sélectionné
if selected_contour is not None:
    # Initialiser le tracker avec le contour sélectionné
    x, y, w, h = cv2.boundingRect(selected_contour)
    tracker = cv2.TrackerKCF_create()
    tracker.init(frame, (x, y, w, h))

    while True:
        # Lire la frame suivante
        ret, frame = cap.read()
        if not ret:
            break

        # Mettre à jour le tracker
        success, bbox = tracker.update(frame)

        if success:
            (x, y, w, h) = [int(v) for v in bbox]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        cv2.imshow("Suivi d'objet", frame)

        # Attendre un court instant pour maintenir la vitesse de la vidéo
        if cv2.waitKey(int(1000 / cap.get(cv2.CAP_PROP_FPS))) & 0xFF == 27:  # Échap pour quitter
            break
else:
    print("Aucun objet sélectionné.")

cap.release()
cv2.destroyAllWindows()