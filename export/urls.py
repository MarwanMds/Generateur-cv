from django.urls import path
from . import views

app_name = 'export'

urlpatterns = [
    path('<int:pk>/pdf/', views.export_pdf, name='pdf'),
]
