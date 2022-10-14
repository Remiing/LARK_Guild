from django.urls import path

from . import views

app_name = 'guild'

urlpatterns = [
    path('', views.index, name='index'),
    path('chart/', views.chart, name='chart'),
    path('<str:character_name>/', views.history, name='history')
]
