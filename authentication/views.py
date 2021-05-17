from django.shortcuts import render, redirect
from django.views import View
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from validate_email import validate_email
from django.contrib import messages
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes, force_text, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import token_generator
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib import auth
import threading
# Create your views here.

class EmailThread(threading.Thread):
  def __init__(self, email):
    self.email = email
    return threading.Thread.__init__(self)
  def run(self):
    self.email.send(fail_silently=False)

class RegisterationView(View):
  def get(self, request):
    return render(request, 'authentication/register.html')
  def post(self, request):
    #get user data
    username = request.POST['username']
    email = request.POST['email']
    password = request.POST['password']
    context = {
      'fieldValues': request.POST
    }
    #validate & create
    if not User.objects.filter(username=username).exists():
      if not User.objects.filter(email=email).exists():
        if len(password)<6:
          messages.error(request, 'Password too short.')
          return render(request, 'authentication/register.html',context)
        user = User.objects.create_user(username=username, email=email)
        user.set_password(password)
        user.is_active = False
        user.save()
        email_subject = 'Activate your account'
        # # path_to_view 
        # getting domain we are on 
        # relative url to verification
        # - encode uid
        # - token 
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        domain = get_current_site(request).domain
        link = reverse('activate', kwargs={'uidb64':uidb64, 'token': token_generator.make_token(user)})
        activate_url = 'http://' + domain + link
        email_body = 'Hi ' + user.username + ' Please use this link to verify your account. \n' + activate_url
        email = EmailMessage(
            email_subject,
            email_body,
            'noreply@semicolon.com',
            [email],
           
        )
        # email.send(fail_silently=False)
        EmailThread(email).start()
        messages.success(request, 'Account successfully created')
        return render(request, 'authentication/register.html')
    #create user account

    return render(request, 'authentication/register.html')

class VerificationView(View):
  def get(self, request,uidb64, token):
    try:
      id = force_text(urlsafe_base64_decode(uidb64))
      user = User.objects.get(id=id)
      if not token_generator.check_token(user, token):
        return redirect('login'+'?message=' + 'User already activated')

      if user.is_active:
        return redirect('login')
      user.is_active = True
      user.save()

      messages.success(request, 'Account Activated Successfully.')
      return redirect('login')
    except Exception as ex:
      pass

    return redirect('login')

class LoginView(View):
  def get(self, request):
    return render(request, 'authentication/login.html')
  def post(self, request):
    username = request.POST['username']
    password = request.POST['password']
    if username and password:
      user = auth.authenticate(username=username, password=password)
      if user:
        if user.is_active:
          auth.login(request,user)
          messages.success(request, 'Welcome, ' + username + ' You are now logged in.')
          return redirect('expenses')
        else:
          messages.error(request, 'Account not active. Please check email.')
          return render(request, 'authentication/login.html')
      else:
        messages.error(request, 'Invalid Credentials. Try again.')
        return render(request, 'authentication/login.html')
    else:
      messages.error(request, 'Please fill the fields')
      return render(request, 'authentication/login.html')

class LogoutView(View):
  def post(self, request):
    auth.logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')


class UserNameValidationView(View):
  def post(self, request):
    data = json.loads(request.body)
    username = data['username']
    if not str(username).isalnum():
      return JsonResponse({'username_error': 'Username should only contain alphanumeric characters.' }, status=400)
    
    if User.objects.filter(username=username).exists():
      return JsonResponse({'username_error': 'Sorry, username in use, choose another one.' }, status=409)


    return JsonResponse({'username_valid': True})

class EmailValidationView(View):
  def post(self, request):
    data = json.loads(request.body)
    email = data['email']
    if not validate_email(email):
      return JsonResponse({'email_error': 'Email is invalid.' }, status=400)
    
    if User.objects.filter(email=email).exists():
      return JsonResponse({'email_error': 'Sorry, email in use, choose another one.' }, status=409)


    return JsonResponse({'email_valid': True})


class RequestPasswordResetEmail(View):
  def get(self, request):
    return render(request, 'authentication/reset-password.html')
  def post(self, request):
    email = request.POST['email']
    context = {
      'values': request.POST
    }
    if not validate_email(email):
      messages.error(request, 'Please give a valid email')
      return render(request, 'authentication/reset-password.html', context)

    user = User.objects.filter(email=email)
    if user.exists():
      user = user[0]
      # print(user.username)
      email_subject = 'Password Reset Instructions'
      uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
      domain = get_current_site(request).domain
      link = reverse('reset-user-password', kwargs={'uidb64':uidb64, 'token': PasswordResetTokenGenerator().make_token(user)})
      reset_url = 'http://' + domain + link
      email_body = 'Hi there, Please use this link to reset your account password. \n' + reset_url
      email = EmailMessage(
          email_subject,
          email_body,
          'noreply@semicolon.com',
          [email],
          
      )
      # email.send(fail_silently=False)
      EmailThread(email).start()
    messages.success(request, 'We have sent you an email to reset password.')
    
    return render(request, 'authentication/reset-password.html')
  
class CompletePasswordReset(View):
  def get(self, request, uidb64, token):
    context = {
      'uidb64':uidb64, 
      'token': token
    }

    try:
      id = force_text(urlsafe_base64_decode(uidb64))
      user = User.objects.get(id=id)
      if not PasswordResetTokenGenerator().check_token(user, token):
        messages.info(request, 'Password link is invalid. Please request a new one.')
        return redirect('request-password')
    except Exception as identifier:
      messages.info(request, 'Something went wrong')

    return render(request, 'authentication/set-newpassword.html', context)
  def post(self, request, uidb64, token):
    context = {
      'uidb64':uidb64, 
      'token': token
    }
    password = request.POST['password']
    password2 = request.POST['password2']
    if password!=password2:
      messages.error(request, 'passwords do not match')
      return render(request, 'authentication/set-newpassword.html', context)
    if len(password)<6:
      messages.error(request, 'passwords should be atleast 6 characters.')
      return render(request, 'authentication/set-newpassword.html', context)
    try:
      id = force_text(urlsafe_base64_decode(uidb64))
      user = User.objects.get(id=id)
      user.set_password(password)
      user.save()
      messages.success(request, 'Password reset successfully. Login with new password.')
      return redirect('login')
    except Exception as identifier:
      messages.info(request, 'Something went wrong')

    
      return render(request, 'authentication/set-newpassword.html', context)
    
    

