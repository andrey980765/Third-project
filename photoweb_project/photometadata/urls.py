from django.urls import path
from . import views

app_name = 'photometadata'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('files/', views.list_files_view, name='list_files'),
    path('files/detail/', views.file_detail, name='file_detail'),
]
