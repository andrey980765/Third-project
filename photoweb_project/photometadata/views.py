import os
import json
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from .forms import PhotoMetaForm, UploadFileForm

DATA_FILE = os.path.join(settings.MEDIA_ROOT, "photos.json")

def load_existing_data():
    """Загрузка данных из основного JSON файла."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_data(data_list):
    """Сохранение данных в основной JSON файл."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2, default=str)

def index(request):
    """Главная страница: форма добавления и загрузка файлов."""
    form = PhotoMetaForm()
    upload_form = UploadFileForm()
    message = ""

    data_list = load_existing_data()

    if request.method == "POST":
        if "save_json" in request.POST:
            form = PhotoMetaForm(request.POST)
            if form.is_valid():
                new_entry = form.cleaned_data
                # tags как список
                tags = [t.strip() for t in new_entry.get('tags', '').split(',') if t.strip()]
                if tags:
                    new_entry['tags'] = tags
                save_data(data_list + [new_entry])
                messages.success(request, " Данные успешно добавлены!")
                return redirect('photometadata:index')
            else:
                messages.error(request, " Проверьте корректность введённых данных.")

    return render(request, "photometadata/index.html", {
        "form": form,
        "upload_form": upload_form,
        "data_list": data_list
    })

def upload_file(request):
    """Обработчик загрузки JSON файла."""
    if request.method != 'POST':
        return redirect('photometadata:index')

    form = UploadFileForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "Ошибка формы загрузки.")
        return redirect('photometadata:index')

    f = form.cleaned_data['file']
    content = f.read()
    try:
        text = content.decode('utf-8')
    except Exception:
        messages.error(request, "Файл должен быть в кодировке UTF-8.")
        return redirect('photometadata:index')

    try:
        obj = json.loads(text)
    except Exception as e:
        messages.error(request, f"JSON parse error: {e}")
        return redirect('photometadata:index')

    if not isinstance(obj, list):
        messages.error(request, "JSON файл должен содержать список объектов.")
        return redirect('photometadata:index')

    data_list = load_existing_data()
    save_data(data_list + obj)
    messages.success(request, " JSON успешно загружен и объединён с существующими данными!")
    return redirect('photometadata:list_files')

def list_files_view(request):
    """Показать существующий JSON-файл."""
    exists = os.path.exists(DATA_FILE)
    return render(request, 'photometadata/list_files.html', {
        'json_file_exists': exists,
        'json_file_name': os.path.basename(DATA_FILE) if exists else None
    })

def file_detail(request):
    """Просмотр содержимого JSON-файла."""
    if not os.path.exists(DATA_FILE):
        messages.error(request, "Файл не найден.")
        return redirect('photometadata:list_files')

    with open(DATA_FILE, encoding='utf-8') as f:
        data = json.load(f)

    return render(request, 'photometadata/file_detail.html', {
        'parsed': data,
        'fname': os.path.basename(DATA_FILE),
        'ftype': 'json'
    })

