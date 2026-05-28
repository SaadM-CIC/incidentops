from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardRedirectView.as_view(), name='index'),
    path('user/', views.UserDashboardView.as_view(), name='user'),
    path('technicien/', views.TechnicienDashboardView.as_view(), name='technicien'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin'),
]
