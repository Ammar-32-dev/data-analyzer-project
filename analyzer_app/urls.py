from django.urls import path
from . import views

app_name = 'analyzer_app'

urlpatterns = [
    path('', views.upload_file, name='upload_file'),
    path('download_plot/<int:plot_index>/', views.download_plot, name='download_plot'),
    path('download_summary/<str:summary_type>/', views.download_summary, name='download_summary'),
    path('download_data/<str:data_type>/', views.download_data, name='download_data'),
    path('download_all_plots/', views.download_all_plots, name='download_all_plots'),
]
