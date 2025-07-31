from django.urls import path
from . import views

app_name = 'submit'

urlpatterns = [
    path('', views.submit, name='submit'),
    path('api/submit/', views.api_submit, name='api_submit'),
] 