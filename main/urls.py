from django.urls import path
from . import views


urlpatterns=[
    path('',views.landing_page,name='landing_page'),
    path('auth/', views.auth_page, name='auth_page'),
    path('dashboard',views.dashboard,name='dashboard'),
    path('download/<int:upload_id>/', views.download_upload, name='download_upload'),
    path('delete/<int:upload_id>/', views.delete_upload, name='delete_upload'),
    path('logout/', views.logout_view, name='logout'),
]
