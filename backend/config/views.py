from django.shortcuts import render

def index(request):
    return render(request, 'pages/library.html')

def ask(request):
    return render(request, 'pages/ask.html')

def history(request):
    return render(request, 'pages/history.html')
