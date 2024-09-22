from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app_autenticacao.urls')), 
    path('', include('app_estoque_mp.urls')), 
    path('', include('app_inspecao.urls')), 
]
