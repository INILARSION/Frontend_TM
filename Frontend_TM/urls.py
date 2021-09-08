from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('run_tm/', views.run_tm, name='run_tm'),
]
