from .views import RegisterationView, UserNameValidationView, EmailValidationView, VerificationView, LoginView, LogoutView, RequestPasswordResetEmail,CompletePasswordReset
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('register', RegisterationView.as_view(), name='register'),
    path('validate-username',csrf_exempt(UserNameValidationView.as_view()), name='validate-username'),
    path('validate-email',csrf_exempt(EmailValidationView.as_view()), name='validate-email'),
    path('activate/<uidb64>/<token>',csrf_exempt(VerificationView.as_view()), name='activate'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('request-password', RequestPasswordResetEmail.as_view(), name='request-password'),
    path('reset-user-password/<uidb64>/<token>', CompletePasswordReset.as_view(), name='reset-user-password'),

    





]
