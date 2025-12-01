from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('prestamos/', views.prestamo_lista, name='prestamo_lista'),
    path('prestamos/crear/', views.prestamo_crear, name='prestamo_crear'),
    path('prestamos/<int:pk>/', views.prestamo_detalle, name='prestamo_detalle'),
    path('prestamos/<int:pk>/editar/', views.prestamo_editar, name='prestamo_editar'),
    path('prestamos/<int:pk>/eliminar/', views.prestamo_eliminar, name='prestamo_eliminar'),
    path('amortizacion/<int:pk>/actualizar/', views.amortizacion_actualizar, name='amortizacion_actualizar'),
]