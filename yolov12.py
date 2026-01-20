from ultralytics import YOLO

# Load a pretrained YOLO26n model
model = YOLO(r"yolo26m-pose (1).pt")

# Run inference on 'bus.jpg' with arguments
model.track(source=r"short2.mp4", show=True, save=True, save_txt=True)