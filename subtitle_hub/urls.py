from django.contrib import admin
from django.urls import path
from catalogue import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('work/<int:work_id>/', views.work_detail, name='work_detail'),
    path('download/<int:entry_id>/', views.download, name='download'),
]
