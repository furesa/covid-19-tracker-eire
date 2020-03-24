from django.shortcuts import render


def map_app(request):
    return render(request, 'map_app.html', {})
