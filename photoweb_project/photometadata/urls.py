from django.urls import path
from . import views

app_name = 'photometadata'

urlpatterns = [
    path('', views.index, name='index'),                          # форма + загрузка
    path('upload/', views.upload_file, name='upload_file'),       # отдельно загрузка (опционально)
    path('files/', views.list_files_view, name='list_files'),     # список файлов
    path('files/<str:ftype>/<str:fname>/', views.file_detail, name='file_detail'),  # просмотр
]
