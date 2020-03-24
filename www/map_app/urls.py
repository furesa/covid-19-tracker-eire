from django.urls import path
from map_app import views


urlpatterns = [
    path('', views.map_app, name='map_app'),
]
