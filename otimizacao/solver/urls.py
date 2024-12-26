from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('optimize/', views.optimize, name='optimize'),
    path('graph/', views.graph, name='graph'),
]