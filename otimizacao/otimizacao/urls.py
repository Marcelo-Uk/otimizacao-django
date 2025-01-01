from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def redirect_to_solver(request):
    return redirect('/solver/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('solver/', include('solver.urls')),
    path('', redirect_to_solver),
]