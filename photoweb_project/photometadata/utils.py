import os
import uuid
import json
from datetime import datetime
import xml.etree.ElementTree as ET

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

# -----------------------
# Конфигурация валидации
# -----------------------
REQUIRED_FIELDS = {
    "title": str,
    "photographer": str,
    "date_taken": str,  # ISO YYYY-MM-DD
    "url": str
}

OPTIONAL_FIELDS = {
    "description": str,
    "location": str,
    "tags": list,
    "width": int,
    "height": int,
    "camera": str,
    "license": str
}

# -----------------------
# Утилиты безопасности
# -----------------------
def generate_secure_filename(ext: str) -> str:
    """Сгенерировать уникальное безопасное имя файла (uuid + .ext)."""
    return f"{uuid.uuid4().hex}.{ext}"

def ensure_dirs(base_dir):
    """Создаёт подпапки json и xml, если их нет."""
    os.makedirs(os.path.join(base_dir, 'json'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'xml'), exist_ok=True)

# -----------------------
# Проверки
# -----------------------
def validate_date_iso(s: str):
    """Проверяем формат YYYY-MM-DD."""
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True, ""
    except Exception as e:
        return False, str(e)

def validate_url(u: str):
    """Django URLValidator — проверка URL."""
    validator = URLValidator()
    try:
        validator(u)
        return True, ""
    except ValidationError as e:
        return False, str(e)

def validate_json_data(obj: dict):
    """
    Валидация JSON-объекта по простым правилам:
    - верхний уровень — dict
    - обязательные поля присутствуют и того типа
    - date и url проходят дополнительные проверки
    Возвращает (is_valid: bool, errors: list[str])
    """
    errors = []
    if not isinstance(obj, dict):
        return False, ["Top-level JSON must be an object (dict)"]

    # required
    for k, ktype in REQUIRED_FIELDS.items():
        if k not in obj:
            errors.append(f"Missing required field: {k}")
        else:
            if not isinstance(obj[k], ktype):
                errors.append(f"Field {k} must be of type {ktype.__name__}")

    # date format
    if "date_taken" in obj:
        ok, msg = validate_date_iso(obj["date_taken"])
        if not ok:
            errors.append(f"date_taken must be YYYY-MM-DD. Error: {msg}")

    # url
    if "url" in obj:
        ok, msg = validate_url(obj["url"])
        if not ok:
            errors.append(f"url is invalid. Error: {msg}")

    # optional fields
    for k, ktype in OPTIONAL_FIELDS.items():
        if k in obj:
            if ktype == list:
                if not isinstance(obj[k], list):
                    errors.append(f"{k} must be a list")
                else:
                    for i, it in enumerate(obj[k]):
                        if not isinstance(it, str):
                            errors.append(f"{k}[{i}] must be string")
            else:
                if not isinstance(obj[k], ktype):
                    errors.append(f"{k} must be of type {ktype.__name__}")

    return (len(errors) == 0), errors

# -----------------------
# XML parsing
# -----------------------
def parse_and_validate_xml_string(xml_string: str):
    """
    Ожидаемый формат XML:
    <photo>
      <title>...</title>
      <photographer>...</photographer>
      <date_taken>YYYY-MM-DD</date_taken>
      <url>...</url>
      <tags><tag>a</tag><tag>b</tag></tags>
      ...
    </photo>
    Возвращаем (ok:bool, errors:list, data:dict_or_None)
    """
    errors = []
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        return False, [f"XML parse error: {e}"], None

    if root.tag != 'photo':
        errors.append("Root element must be <photo>")

    def get_text(tag):
        el = root.find(tag)
        return el.text.strip() if (el is not None and el.text) else None

    data = {}
    data['title'] = get_text('title')
    data['photographer'] = get_text('photographer')
    data['date_taken'] = get_text('date_taken')
    data['url'] = get_text('url')
    data['description'] = get_text('description')
    data['location'] = get_text('location')
    data['camera'] = get_text('camera')
    data['license'] = get_text('license')

    # tags
    tags_el = root.find('tags')
    tags = []
    if tags_el is not None:
        for t in tags_el.findall('tag'):
            if t.text:
                tags.append(t.text.strip())
    if tags:
        data['tags'] = tags

    # width/height
    w = get_text('width')
    h = get_text('height')
    if w:
        try:
            data['width'] = int(w)
        except:
            errors.append("width must be integer")
    if h:
        try:
            data['height'] = int(h)
        except:
            errors.append("height must be integer")

    # required checks
    for k in ['title','photographer','date_taken','url']:
        if not data.get(k):
            errors.append(f"Missing required element: {k}")

    # date/url validation
    if data.get('date_taken'):
        ok, msg = validate_date_iso(data['date_taken'])
        if not ok:
            errors.append(f"date_taken must be YYYY-MM-DD. Error: {msg}")
    if data.get('url'):
        ok, msg = validate_url(data['url'])
        if not ok:
            errors.append(f"url is invalid. Error: {msg}")

    return (len(errors) == 0), errors, data

# -----------------------
# Чтение/запись файлов
# -----------------------
def save_json_to_file(base_dir: str, data_obj: dict):
    ensure_dirs(base_dir)
    fname = generate_secure_filename('json')
    path = os.path.join(base_dir, 'json', fname)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data_obj, f, ensure_ascii=False, indent=2)
    return fname, path

def save_xml_to_file(base_dir: str, xml_string: str):
    ensure_dirs(base_dir)
    fname = generate_secure_filename('xml')
    path = os.path.join(base_dir, 'xml', fname)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(xml_string)
    return fname, path

def list_files(base_dir: str):
    ensure_dirs(base_dir)
    j = [f for f in os.listdir(os.path.join(base_dir,'json')) if f.endswith('.json')]
    x = [f for f in os.listdir(os.path.join(base_dir,'xml')) if f.endswith('.xml')]
    return j, x

def read_json_file(base_dir: str, filename: str):
    p = os.path.join(base_dir, 'json', filename)
    with open(p, encoding='utf-8') as f:
        return json.load(f)

def read_xml_file(base_dir: str, filename: str):
    p = os.path.join(base_dir, 'xml', filename)
    with open(p, encoding='utf-8') as f:
        return f.read()
