from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('', views.home, name='home'),
    path('<int:year>/', views.team_detail, name='team_detail'),
    path('<int:year>/stickers/', views.sticker_spread, name='sticker_spread'),
    path('whatsapp/', views.whatsapp_modal, name='whatsapp_modal'),
    path('sticker/<int:pk>/', views.sticker_modal, name='sticker_modal'),
    path('sticker/<int:pk>/add/', views.add_sticker, name='add_sticker'),
    path('sticker/<int:pk>/update/', views.update_sticker, name='update_sticker'),
    path('sticker/<int:pk>/remove', views.remove_sticker, name='remove_sticker'),
    path('register/', views.register, name='register'),
]
