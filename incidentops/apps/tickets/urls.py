from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.TicketListView.as_view(), name='list'),
    path('create/', views.TicketCreateView.as_view(), name='create'),
    path('<int:pk>/', views.TicketDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.TicketEditView.as_view(), name='edit'),
    path('<int:pk>/status/', views.TicketStatusUpdateView.as_view(), name='status_update'),
    path('<int:pk>/assign/', views.TicketAssignView.as_view(), name='assign'),
]