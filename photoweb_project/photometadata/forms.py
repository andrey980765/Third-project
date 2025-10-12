from django import forms

class PhotoMetaForm(forms.Form):
    """
    Форма для ввода метаданных о фото.
    Поля: обязательные и необязательные.
    """
    title = forms.CharField(max_length=200, label="Название")
    photographer = forms.CharField(max_length=200, label="Фотограф")
    date_taken = forms.DateField(
        input_formats=['%Y-%m-%d'],
        label="Дата съемки (YYYY-MM-DD)",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    url = forms.URLField(label="URL изображения")
    description = forms.CharField(widget=forms.Textarea, required=False)
    location = forms.CharField(max_length=200, required=False)
    tags = forms.CharField(required=False, help_text="Через запятую")
    width = forms.IntegerField(required=False, min_value=0)
    height = forms.IntegerField(required=False, min_value=0)
    camera = forms.CharField(max_length=200, required=False)
    license = forms.CharField(max_length=200, required=False)

class UploadFileForm(forms.Form):
    """
    Простая форма загрузки файла.
    Мы не доверяем имени файла, только содержимому.
    """
    file = forms.FileField(label="Файл JSON или XML")
