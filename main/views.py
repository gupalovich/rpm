from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect


def signup(request):
    return render(request, 'registration.html')


def signin(request):
    return render(request, 'sign_in.html')


###############################
def home(request):
    response = redirect('signin')
    return response


def dashboard(request):
    return render(request, 'dashboard.html')


def token(request):
    return render(request, 'token.html')


def team(request):
    return render(request, 'team.html')


def profile(request):
    return render(request, 'profile.html')
