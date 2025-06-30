from django.urls import path, include
from accounts.views import register_user, login_user, logout_user, SignUpView, hello_world, get_problem, get_problems

urlpatterns = [
    path("hello/", hello_world, name="hello-world"),
    path("register/", register_user, name="register-user"),
    path("login/", login_user, name="login-user"),
    path("logout/", logout_user, name="logout-user"),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('problem/<int:problem_id>/', get_problem, name='get-problem'),
    path('problems/', get_problems, name='get-problems'),
]
