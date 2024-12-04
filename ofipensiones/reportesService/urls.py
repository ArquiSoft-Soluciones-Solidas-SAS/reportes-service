from django.urls import path
from .views import generar_reporte#,generar_cartera

app_name = 'manejador_reportes'  # Esto es necesario para el namespace
urlpatterns = [
    path('', generar_reporte, name='generar_reporte'),
    path('reporte/<str:nombre_institucion>/<str:mes>/', generar_reporte, name='generar_reporte'),
    #path('cartera_general/<str:nombre_institucion>/<str:mes>/', generar_cartera, name='generar_cartera'),
]
