from django.urls import path
from .views import generar_reporte, listar_instituciones  # ,generar_cartera

app_name = 'manejador_reportes'  # Esto es necesario para el namespace
urlpatterns = [
    path('', generar_reporte, name='generar_reporte'),
    path('reporte/<str:nombre_institucion>/<str:mes>/', generar_reporte, name='generar_reporte'),
    path('reporte/instituciones/', listar_instituciones, name='listar_instituciones'),
]
