from django.urls import path
from . import views

app_name = 'cv'

urlpatterns = [
    path('new/',                          views.cv_new,       name='new'),
    path('<int:pk>/step/<int:step>/',     views.cv_step,      name='step'),
    path('<int:pk>/delete/',              views.cv_delete,    name='delete'),
    path('<int:pk>/autosave/<int:step>/', views.cv_autosave,  name='autosave'),
]
