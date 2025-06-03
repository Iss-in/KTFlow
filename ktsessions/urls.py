from django.urls import path
from . import views

urlpatterns = [
    # Class-based views
    # path('kt-sessions/', views.KTSessionListCreateView.as_view(), name='kt-session-list-create'),
    # path('kt-sessions/<int:pk>/', views.KTSessionDetailView.as_view(), name='kt-session-detail'),

    # Function-based views (alternative)
    path('kt-sessions/', views.kt_session_list_create, name='kt-session-list-create'),
    path('kt-sessions/<int:pk>/', views.kt_session_detail, name='kt-session-detail'),

    # Public share view
    path('kt-sessions/shared/<uuid:share_token>/', views.kt_session_by_token, name='kt-session-by-token'),

    path('attachments/', views.get_attachments, name='get_attachments'),
    path('attachments/create/', views.create_attachment, name='create_attachment'),
    path('attachments/<int:attachment_id>/', views.get_attachment, name='get_attachment'),
    path('attachments/<int:attachment_id>/update/', views.update_attachment, name='update_attachment'),
    path('attachments/<int:attachment_id>/delete/', views.delete_attachment, name='delete_attachment'),

    # Session-specific attachments
    path('sessions/<int:session_id>/attachments/', views.get_session_attachments, name='get_session_attachments'),
]