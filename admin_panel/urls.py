from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('',                        views.overview,          name='overview'),
    path('users/',                  views.users_list,        name='users_list'),
    path('users/<int:user_id>/',    views.user_detail,       name='user_detail'),
    path('users/<int:user_id>/delete/',       views.user_delete,       name='user_delete'),
    path('users/<int:user_id>/toggle-staff/', views.user_toggle_staff, name='user_toggle_staff'),
    path('cvs/',                    views.cvs_list,          name='cvs_list'),
    path('cvs/<int:cv_id>/preview/', views.cv_preview,        name='cv_preview'),
    path('cvs/<int:cv_id>/delete/', views.cv_delete,         name='cv_delete'),
]