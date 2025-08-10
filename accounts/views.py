from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import UserSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Problem, TestCase
from django.conf import settings
from pathlib import Path

# Create your views here.

@api_view(['GET'])
@permission_classes([AllowAny])
def hello_world(request):
    return Response({"message": "Hello, world!"})

@csrf_exempt
def register_user(request):

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'status': 'error', 'message': 'Username and password are required'}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({'status': 'error', 'message': 'User with this username already exists'}, status=400)
            
            user = User.objects.create_user(username=username)

            user.set_password(password)

            user.save()
            
            return JsonResponse({'status': 'success', 'message': 'User created successfully'}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)
    
    
@csrf_exempt
def login_user(request):

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'status': 'error', 'message': 'Username and password are required'}, status=400)

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request,user)
                return JsonResponse({'status': 'success', 'message': 'login successful'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)

@csrf_exempt
def logout_user(request):
    if request.method == "POST":
        logout(request)
        return JsonResponse({'status': 'success', 'message': 'logout successful'})
    return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)

class SignUpView(generics.CreateAPIView):
    """
    A view for creating a new user.
    This view is open to any user (authentication is not required).
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def get_problems(request):
    problems = Problem.objects.all()
    problem_list = []
    for problem in problems:
        desc = ""
        if problem.problem_file:
            try:
                with open(problem.problem_file, 'r', encoding='utf-8') as f:
                    desc = f.read(100)
            except Exception:
                desc = ""
        problem_list.append({
            'id': problem.id,
            'title': problem.title,
            'description': desc,
            'difficulty': problem.difficulty,
            'tags': problem.tags.split(',') if problem.tags else [],
        })
    return Response(problem_list)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_problem(request, problem_id):
    try:
        problem = Problem.objects.get(id=problem_id)
        testcase = TestCase.objects.filter(problem=problem).first()
        # Prefer file description; fallback to DB field
        description = ""
        try:
            if problem.problem_file:
                with open(problem.problem_file, 'r', encoding='utf-8') as f:
                    description = f.read()
        except Exception:
            description = ""
        if not description:
            description = problem.description or ""
        # Prefer TestCase files; fallback to filesystem testcases/<uuid>/<uuid>.in|.out
        sample_input = ""
        sample_output = ""
        try:
            if testcase and testcase.input_file:
                with open(testcase.input_file, 'r', encoding='utf-8') as f:
                    sample_input = f.read()
            if testcase and testcase.output_file:
                with open(testcase.output_file, 'r', encoding='utf-8') as f:
                    sample_output = f.read()
        except Exception:
            pass
        if not sample_input or not sample_output:
            tc_dir = Path(settings.BASE_DIR) / 'testcases' / str(problem.id)
            in_path = tc_dir / f"{problem.id}.in"
            out_path = tc_dir / f"{problem.id}.out"
            try:
                if in_path.exists() and not sample_input:
                    sample_input = in_path.read_text(encoding='utf-8')
                if out_path.exists() and not sample_output:
                    sample_output = out_path.read_text(encoding='utf-8')
            except Exception:
                pass
        return Response({
            'id': problem.id,
            'title': problem.title,
            'description': description,
            'sample_input': sample_input,
            'sample_output': sample_output,
            'difficulty': problem.difficulty,
            'tags': problem.tags.split(',') if problem.tags else [],
        })
    except Problem.DoesNotExist:
        return Response({'error': 'Problem not found'}, status=404)