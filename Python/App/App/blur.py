import sys
import cv2
import mediapipe as mp
import os

def blur_faces_in_video(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Input file '{input_path}' does not exist.")
        return

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Failed to open video: {input_path}")
        return

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    mp_face_detection = mp.solutions.face_detection

    with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb_frame)

            if results.detections:
                for detection in results.detections:
                    bboxC = detection.location_data.relative_bounding_box
                    ih, iw, _ = frame.shape
                    x = int(bboxC.xmin * iw)
                    y = int(bboxC.ymin * ih)
                    w = int(bboxC.width * iw)
                    h = int(bboxC.height * ih)
                    x, y = max(0, x), max(0, y)
                    w, h = min(iw - x, w), min(ih - y, h)
                    face = frame[y:y+h, x:x+w]
                    face = cv2.GaussianBlur(face, (99, 99), 30)
                    frame[y:y+h, x:x+w] = face

            out.write(frame)

    cap.release()
    out.release()
    print(f"Done! Output saved as {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python blur_faces.py input.mp4 output.mp4")
    else:
        blur_faces_in_video(sys.argv[1], sys.argv[2])
