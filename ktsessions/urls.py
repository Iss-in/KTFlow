from django.urls import path
from . import views

urlpatterns = [
    path('kt-sessions/', views.kt_session_list_create, name='kt_session_list_create'),
    path('kt-sessions/<int:pk>/', views.kt_session_detail, name='kt_session_detail'),

    # Public share view
    path('kt-sessions/get_sharing_url/<int:pk>/', views.get_sharing_url, name='get_sharing_url'),
    path('kt-sessions/get_by_url/<str:share_token>/', views.kt_session_by_url, name='kt_session_by_url'),

    path('attachments/', views.get_attachments, name='get_attachments'),
    path('attachments/create/', views.create_attachment, name='create_attachment'),
    path('attachments/<int:attachment_id>/', views.get_attachment, name='get_attachment'),
    path('attachments/<int:attachment_id>/update/', views.update_attachment, name='update_attachment'),
    path('attachments/<int:attachment_id>/delete/', views.delete_attachment, name='delete_attachment'),

]