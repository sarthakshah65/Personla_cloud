from django.shortcuts import render,redirect,get_object_or_404
#import django.contrib.auth as auth
#from django.contrib.auth.models import User
#from django.contrib import messages
#from .models import chatRoom,Messages,FriendsList,RequestList
#import string,random,json
# Create your views here.

def landing_page(request):
    return render(request,'index.html')


def auth_page(request):
    return render(request, 'auth.html')
