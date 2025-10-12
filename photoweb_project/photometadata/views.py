import os
import json
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages

from .forms import PhotoMetaForm, UploadFileForm
from . import utils

# BASE_DIR_FILES — папка, где будут храниться json/xml, берем из settings.MEDIA_ROOT
BASE_DIR_FILES = getattr(settings, 'MEDIA_ROOT', None)
if not BASE_DIR_FILES:
    BASE_DIR_FILES = os.path.join(settings.BASE_DIR, 'media')  # fallback

def index(request):
    """
    Главная страница:
    - показываем форму ввода метаданных
    - обрабатываем сохранение в JSON или XML (кнопки)
    - форма для загрузки файла (внизу)
    """
    if request.method == 'POST' and 'save_json' in request.POST or request.method == 'POST' and 'save_xml' in request.POST:
        # пришла форма ввода
        form = PhotoMetaForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # собираем json-объект
            tags = [t.strip() for t in cd.get('tags','').split(',') if t.strip()]
            data_obj = {
                "title": cd['title'],
                "photographer": cd['photographer'],
                "date_taken": cd['date_taken'].isoformat(),
                "url": cd['url']
            }
            # добавить необязательные поля, если заданы
            for opt in ['description','location','camera','license','width','height']:
                v = cd.get(opt)
                if v not in (None, ''):
                    data_obj[opt] = v
            if tags:
                data_obj['tags'] = tags

            # серверная валидация json-данных
            is_valid, errors = utils.validate_json_data(data_obj)
            if not is_valid:
                messages.error(request, "Данные не прошли валидацию: " + "; ".join(errors))
            else:
                # определяем, какую кнопку нажали
                if 'save_json' in request.POST:
                    fname, path = utils.save_json_to_file(BASE_DIR_FILES, data_obj)
                    messages.success(request, f"JSON сохранён: {fname}")
                else:  # save_xml
                    from xml.etree.ElementTree import Element, SubElement, tostring
                    root = Element('photo')
                    def add(tag, val):
                        el = SubElement(root, tag)
                        el.text = str(val)
                    # добавляем обязательные/необязательные
                    add('title', data_obj['title'])
                    add('photographer', data_obj['photographer'])
                    add('date_taken', data_obj['date_taken'])
                    add('url', data_obj['url'])
                    for k in ['description','location','camera','license','width','height']:
                        if k in data_obj:
                            add(k, data_obj[k])
                    if 'tags' in data_obj:
                        tags_el = SubElement(root, 'tags')
                        for t in data_obj['tags']:
                            t_el = SubElement(tags_el, 'tag')
                            t_el.text = t
                    xml_string = tostring(root, encoding='unicode')
                    fname, path = utils.save_xml_to_file(BASE_DIR_FILES, xml_string)
                    messages.success(request, f"XML сохранён: {fname}")
                return redirect('photometadata:index')
    else:
        form = PhotoMetaForm()

    upload_form = UploadFileForm()
    return render(request, 'photometadata/index.html', {
        'form': form,
        'upload_form': upload_form
    })

def upload_file(request):
    """
    Отдельный обработчик загрузки файла (если используешь отдельный route).
    - читаем файл,
    - определяем JSON или XML по содержимому (не доверяем расширению),
    - валидируем,
    - при валидности сохраняем в папку с сгенерированным именем,
    - при невалидности — не сохраняем и показываем сообщение.
    """
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

    # определяем формат по началу файла/енху
    is_xml = text.lstrip().startswith('<?xml') or '<photo' in text[:200]
    if is_xml:
        ok, errors, data = utils.parse_and_validate_xml_string(text)
        if not ok:
            messages.error(request, "Загруженный XML невалиден: " + "; ".join(errors))
            return redirect('photometadata:index')
        fname, path = utils.save_xml_to_file(BASE_DIR_FILES, text)
        messages.success(request, f"XML успешно загружен: {fname}")
    else:
        try:
            obj = json.loads(text)
        except Exception as e:
            messages.error(request, f"JSON parse error: {e}")
            return redirect('photometadata:index')
        ok, errors = utils.validate_json_data(obj)
        if not ok:
            messages.error(request, "JSON невалиден: " + "; ".join(errors))
            return redirect('photometadata:index')
        fname, path = utils.save_json_to_file(BASE_DIR_FILES, obj)
        messages.success(request, f"JSON успешно загружен: {fname}")

    return redirect('photometadata:list_files')

def list_files_view(request):
    """Показать все существующие файлы (json + xml)."""
    jfiles, xfiles = utils.list_files(BASE_DIR_FILES)
    if not jfiles and not xfiles:
        messages.info(request, "Нет JSON или XML файлов на сервере.")
    return render(request, 'photometadata/list_files.html', {'jfiles': jfiles, 'xfiles': xfiles})

def file_detail(request, ftype, fname):
    """
    Просмотр содержимого конкретного файла.
    ftype: 'json' или 'xml'
    fname: имя файла
    """
    if ftype not in ('json','xml'):
        messages.error(request, "Неверный тип файла")
        return redirect('photometadata:list_files')

    folder = os.path.join(BASE_DIR_FILES, ftype)
    path = os.path.join(folder, fname)
    if not os.path.exists(path):
        messages.error(request, "Файл не найден")
        return redirect('photometadata:list_files')

    parsed = None
    raw = None
    if ftype == 'json':
        try:
            with open(path, encoding='utf-8') as fh:
                parsed = json.load(fh)
        except Exception as e:
            messages.error(request, f"Ошибка чтения JSON: {e}")
    else:
        try:
            with open(path, encoding='utf-8') as fh:
                raw = fh.read()
            ok, errors, data = utils.parse_and_validate_xml_string(raw)
            if ok:
                parsed = data
            else:
                messages.warning(request, "XML файл невалиден при перерасчёте: " + "; ".join(errors))
        except Exception as e:
            messages.error(request, f"Ошибка чтения XML: {e}")

    return render(request, 'photometadata/file_detail.html', {
        'ftype': ftype, 'fname': fname, 'parsed': parsed, 'raw': raw
    })

