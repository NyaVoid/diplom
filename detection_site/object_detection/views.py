import os
import cv2
import numpy as np
from pathlib import Path
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from .models import ImageFeed
from .forms import ImageUploadForm, UserRegistrationForm
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Список классов для распознавания
classes = [
    'cat', 'dog'
]

@login_required
def dashboard(request):
    """Отображение загруженных изображений для текущего пользователя."""
    images = ImageFeed.objects.filter(user=request.user)
    return render(request, 'object_detection/dashboard.html', {'images': images})

@login_required
def add_image_feed(request):
    """Загрузка и обработка нового изображения."""
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Сохраняем форму с изображением
            image_feed = form.save(commit=False)
            image_feed.user = request.user
            image_feed.save()

            # Обрабатываем изображение
            processed_image_file = process_image(image_feed.image)
            
            # Генерируем уникальное имя для обработанного изображения
            processed_image_name = f"processed_{image_feed.id}.jpg"
            image_feed.processed_image.save(processed_image_name, processed_image_file)
            image_feed.save()

            return redirect('dashboard')
    else:
        form = ImageUploadForm()
    
    return render(request, 'object_detection/add_image_feed.html', {'form': form})

def register(request):
    """Регистрация нового пользователя."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'object_detection/register.html', {'form': form})

def user_login(request):
    """Авторизация пользователя."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'object_detection/login.html', {'error': 'Неверные учетные данные'})

    return render(request, 'object_detection/login.html')

def user_logout(request):
    """Выход из учётной записи."""
    logout(request)
    return redirect('login')

def process_image(image_file):
    """Обработка изображения для обнаружения объектов."""
    base_path = Path(__file__).resolve().parent
    proto_path = base_path / 'mobilenet_ssd_deploy.prototxt'
    model_path = base_path / 'mobilenet_iter_73000.caffemodel'

    if not proto_path.exists() or not model_path.exists():
        raise FileNotFoundError("Файлы модели не найдены.")

    net = cv2.dnn.readNetFromCaffe(str(proto_path), str(model_path))

    # Преобразуем файл изображения в формат, с которым работает OpenCV
    image_data = image_file.read()  # Прочитаем байты изображения
    nparr = np.frombuffer(image_data, np.uint8)  # Преобразуем в массив numpy
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Декодируем изображение
    (h, w) = img.shape[:2]

    # Создаем blob и запускаем нейросеть
    blob = cv2.dnn.blobFromImage(img, 0.007843, (w, h), 127.5)
    net.setInput(blob)
    detections = net.forward()

    boxes = []
    confidences = []
    class_ids = []

    # Перебор всех детекций
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]  # Уровень уверенности для текущего объекта
        if confidence > 0.2:  # Фильтрация объектов с низким уровнем уверенности
            class_id = int(detections[0, 0, i, 1])  # Класс объекта (например, кошка или собака)
            label = f"{classes[class_id]}: {confidence:.2f}"  # Подпись для объекта
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])  # Координаты коробки
            (startX, startY, endX, endY) = box.astype("int")
            boxes.append([startX, startY, endX, endY])
            confidences.append(float(confidence))
            class_ids.append(class_id)

    # Применяем Non-Maximum Suppression
    indices = cv2.dnn.NMSBoxes(boxes, confidences, score_threshold=0.5, nms_threshold=0.4)

    # Если есть обнаруженные объекты
    if len(indices) > 0:
        for i in indices.flatten():
            box = boxes[i]
            (startX, startY, endX, endY) = box
            label = f"{classes[class_ids[i]]}: {confidences[i]:.2f}"
            cv2.rectangle(img, (startX, startY), (endX, endY), (0, 255, 0), 2)  # Рисуем прямоугольник
            cv2.putText(img, label, (startX, startY - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)  # Подпись

    # Сохраняем обработанное изображение в памяти
    processed_image_path = Path('processed_image.jpg')
    cv2.imwrite(str(processed_image_path), img)

    # Читаем изображение обратно как байты и возвращаем его
    with open(str(processed_image_path), 'rb') as f:
        processed_image_data = f.read()

    return ContentFile(processed_image_data)
