from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

def index(request):
    """Landing page view"""
    return render(request, 'index.html')

def login_view(request):
    """Login page view"""
    return render(request, 'login.html')

@login_required
def dashboard(request):
    """Dashboard view - requires authentication"""
    return render(request, 'dashboard.html')

def device_join(request, join_token=None):
    """Device joining page"""
    context = {'join_token': join_token}
    return render(request, 'device_join.html', context)