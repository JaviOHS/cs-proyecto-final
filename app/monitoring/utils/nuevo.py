import cv2
import numpy as np

# Cargar el modelo preentrenado MobileNet SSD
net = cv2.dnn.readNetFromCaffe('ruta/del/deploy.prototxt', 'ruta/del/mobilenet_ssd.caffemodel')

# Cargar una imagen de prueba
image = cv2.imread('ruta/de/imagen_prueba.jpg')
(h, w) = image.shape[:2]

# Procesar la imagen para la detección
blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
net.setInput(blob)
detections = net.forward()

# Iterar sobre las detecciones y mostrarlas en la imagen
for i in range(detections.shape[2]):
    confidence = detections[0, 0, i, 2]

    if confidence > 0.2:  # Ajusta el umbral según sea necesario
        idx = int(detections[0, 0, i, 1])
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (startX, startY, endX, endY) = box.astype("int")

        label = f"{idx}: {confidence:.2f}"
        cv2.rectangle(image, (startX, startY), (endX, endY), (0, 255, 0), 2)
        cv2.putText(image, label, (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# Mostrar la imagen con las detecciones
cv2.imshow("Output", image)
cv2.waitKey(0)
cv2.destroyAllWindows()