
from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import render, HttpResponseRedirect
# Create your views here.
def index (request):
    return HttpResponse('hola mundo')

def index_1(request):
    return render(request, "index.html")

def grabaciones(request):
    return render(request,"grabaciones.html")

def interpretes(request):
    return render(request,"interpretes.html")

def companias(request):
    return render(request,"companias.html")

def formatos(request):
    return render(request,"formatos.html")

