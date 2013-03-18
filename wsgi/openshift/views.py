#coding:utf-8
import os
from django.shortcuts import render_to_response
from articles.models import Article
from django.http import HttpResponseRedirect
from django import forms
from django.contrib.auth.models import User, Group
from django.views.decorators.csrf import csrf_protect
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.context_processors import csrf

@csrf_protect
def verify(request):
    if request.method == 'POST':
        c = {}
        reg_errors = ""
        data = request.POST.copy()
        username = data['username']
        password = data['password']
        password2 = data['password2']
        if username == "" or password == "" or password2 == "" :
            reg_errors = u'信息不完整'
            c.update(csrf(request))
        else :
            if password != password2 :
                reg_errors = u'两次密码不匹配'
            else :
                try:
                    User.objects.get(username=username)
                except User.DoesNotExist:
                    user = User.objects.create_user(username= username,password=password)
                    user.is_staff = True
                    user.is_superuser = False
                    user.groups = Group.objects.filter(name="normal user group")
                    user.save()
                    return HttpResponseRedirect("/admin/")
                reg_errors = u'用户名已存在'

        c.update(csrf(request))
        c['reg_errors'] = reg_errors
        return render_to_response('register.html', c)

@csrf_protect   
def register(request):
    c = {}
    c.update(csrf(request))
    return render_to_response('register.html', c)

def home(response):
    return render_to_response('home.html',{})
    
def comment(response):
    return render_to_response('comment.html', {})
    
def about(response):
    return render_to_response('about.html', {})
