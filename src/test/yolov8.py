from ultralytics import YOLO

# Load a YOLOv8n PyTorch model
# model = YOLO('yolov8n.pt')
# model = YOLO('yolov8m.pt')

# Export the model
# model.export(format='openvino')  # creates 'yolov8n_openvino_model/'

# Load the exported OpenVINO model
ov_model = YOLO('yolov8m_openvino_model', task='detect')

# Run inference
for i in range(0, 100):
    results = ov_model('https://ultralytics.com/images/bus.jpg')

