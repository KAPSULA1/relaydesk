from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'rooms', views.RoomViewSet, basename='room')
router.register(r'messages', views.MessageViewSet, basename='message')

app_name = 'chat'

urlpatterns = [
    path('', include(router.urls)),
    path('presence/<slug:room_slug>/', views.room_presence, name='room-presence'),
]
