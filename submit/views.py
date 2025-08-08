from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .forms import CodeSubmissionForm
from django.conf import settings
import os
import uuid
import subprocess
from pathlib import Path
from .models import CodeSubmission


def submit(request):
    if request.method == "POST":
        form = CodeSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save()
            print(submission.language)
            print(submission.code)
            output = run_code(
                submission.language, submission.code, submission.input_data
            )
            submission.output_data = output
            submission.save()
            return render(request, "submit/result.html", {"submission": submission})
    else:
        form = CodeSubmissionForm()
    return render(request, "submit/index.html", {"form": form})


@csrf_exempt
@require_http_methods(["POST"])
def api_submit(request):
    """REST API endpoint for code submission with test case checking"""
    try:
        data = json.loads(request.body)
        language = data.get('language', '').lower()
        code = data.get('code', '')
        problem_id = str(data.get('problem_id', ''))
        # input_data is ignored, we use the test input from file

        # Validate language
        if language not in ['cpp', 'py', 'java']:
            return JsonResponse({
                'error': 'Unsupported language. Supported languages: cpp, py, java'
            }, status=400)

        # Load test input and expected output from files
        testcase_dir = Path(settings.BASE_DIR) / 'testcases' / problem_id
        input_file = testcase_dir / f'{problem_id}.in'
        output_file = testcase_dir / f'{problem_id}.out'
        if not input_file.exists() or not output_file.exists():
            return JsonResponse({'error': 'Testcase files not found for this problem.'}, status=400)
        with open(input_file, 'r', encoding='utf-8') as f:
            test_input = f.read()
        with open(output_file, 'r', encoding='utf-8') as f:
            expected_output = f.read().strip()

        # Run the code with the test input
        user_output = run_code(language, code, test_input).strip()

        # Compare outputs (strip trailing whitespace)
        is_success = user_output == expected_output

        # Save submission to database
        submission = CodeSubmission.objects.create(
            language=language,
            code=code,
            input_data=test_input,
            output_data=user_output
        )

        return JsonResponse({
            'success': is_success,
            'output': user_output,
            'expected_output': expected_output,
            'submission_id': submission.id
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_run(request):
    """REST API endpoint for running code with custom input or test cases"""
    try:
        data = json.loads(request.body)
        language = data.get('language', '').lower()
        code = data.get('code', '')
        problem_id = str(data.get('problem_id', ''))
        custom_input = data.get('custom_input', None)

        # Validate language
        if language not in ['cpp', 'py', 'java']:
            return JsonResponse({
                'error': 'Unsupported language. Supported languages: cpp, py, java'
            }, status=400)

        # Determine input to use
        if custom_input and custom_input.strip():
            # Use custom input provided by user
            input_data = custom_input
        else:
            # Use test case input from file
            testcase_dir = Path(settings.BASE_DIR) / 'testcases' / problem_id
            input_file = testcase_dir / f'{problem_id}.in'
            if not input_file.exists():
                return JsonResponse({'error': 'Testcase files not found for this problem.'}, status=400)
            with open(input_file, 'r', encoding='utf-8') as f:
                input_data = f.read()

        # Run the code with the input
        user_output = run_code(language, code, input_data)

        return JsonResponse({
            'output': user_output,
            'input_used': 'custom' if custom_input and custom_input.strip() else 'testcase'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Server error: {str(e)}'
        }, status=500)


def run_code(language, code, input_data):
    project_path = Path(settings.BASE_DIR)
    directories = ["codes", "inputs", "outputs"]

    for directory in directories:
        dir_path = project_path / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)

    codes_dir = project_path / "codes"
    inputs_dir = project_path / "inputs"
    outputs_dir = project_path / "outputs"

    unique = str(uuid.uuid4())

    code_file_name = f"{unique}.{language}"
    input_file_name = f"{unique}.txt"
    output_file_name = f"{unique}.txt"

    code_file_path = codes_dir / code_file_name
    input_file_path = inputs_dir / input_file_name
    output_file_path = outputs_dir / output_file_name

    try:
        with open(code_file_path, "w") as code_file:
            code_file.write(code)

        with open(input_file_path, "w") as input_file:
            input_file.write(input_data)

        with open(output_file_path, "w") as output_file:
            pass  # This will create an empty file

        if language == "cpp":
            executable_path = codes_dir / f"{unique}.exe"  # Windows executable extension
            compile_result = subprocess.run(
                ["g++", str(code_file_path), "-o", str(executable_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if compile_result.returncode != 0:
                return f"Compilation Error:\n{compile_result.stderr}"
            
            with open(input_file_path, "r") as input_file:
                with open(output_file_path, "w") as output_file:
                    run_result = subprocess.run(
                        [str(executable_path)],
                        stdin=input_file,
                        stdout=output_file,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=5
                    )
                    if run_result.returncode != 0:
                        return f"Runtime Error:\n{run_result.stderr}"
                        
        elif language == "py":
            # Try different Python commands for Windows
            python_commands = ["python", "python3", "py"]
            python_found = False
            
            for cmd in python_commands:
                try:
                    # Test if the command exists
                    test_result = subprocess.run([cmd, "--version"], 
                                               capture_output=True, 
                                               text=True, 
                                               timeout=2)
                    if test_result.returncode == 0:
                        python_cmd = cmd
                        python_found = True
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            if not python_found:
                return "Error: Python interpreter not found. Please install Python and ensure it's in your PATH."
            
            # Code for executing Python script
            with open(input_file_path, "r") as input_file:
                with open(output_file_path, "w") as output_file:
                    run_result = subprocess.run(
                        [python_cmd, str(code_file_path)],
                        stdin=input_file,
                        stdout=output_file,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=5
                    )
                    if run_result.returncode != 0:
                        return f"Runtime Error:\n{run_result.stderr}"

        elif language == "java":
            # Java compilation and execution
            # Use system PATH for Docker environment, fallback to Windows path for local development
            java_compiler = "javac"
            java_runtime = "java"
            
            # Check if Java compiler and runtime exist
            try:
                subprocess.run([java_compiler, "-version"], capture_output=True, text=True, timeout=2)
                subprocess.run([java_runtime, "-version"], capture_output=True, text=True, timeout=2)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return "Error: Java compiler or runtime not found. Please check your JDK installation."
            
            # For Java, we need to ensure the class name matches the file name
            # Extract class name from the code or use a default
            class_name = "Main"  # Default class name
            if "class" in code and "public class" in code:
                # Try to extract class name from the code
                lines = code.split('\n')
                for line in lines:
                    if line.strip().startswith('public class'):
                        class_name = line.strip().split('public class')[1].split()[0].strip()
                        break
            
            # Create Java file with proper class name
            java_file_name = f"{class_name}.java"
            java_file_path = codes_dir / java_file_name
            
            # Write the Java code to file
            with open(java_file_path, "w") as java_file:
                java_file.write(code)
            
            # Compile Java code
            compile_result = subprocess.run(
                [java_compiler, str(java_file_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if compile_result.returncode != 0:
                return f"Compilation Error:\n{compile_result.stderr}"
            
            # Run the compiled Java program
            class_file_path = codes_dir / f"{class_name}.class"
            with open(input_file_path, "r") as input_file:
                with open(output_file_path, "w") as output_file:
                    run_result = subprocess.run(
                        [java_runtime, "-cp", str(codes_dir), class_name],
                        stdin=input_file,
                        stdout=output_file,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=5
                    )
                    if run_result.returncode != 0:
                        return f"Runtime Error:\n{run_result.stderr}"

        # Read the output from the output file
        with open(output_file_path, "r") as output_file:
            output_data = output_file.read()

        return output_data if output_data else "Program executed successfully (no output)"

    except subprocess.TimeoutExpired:
        return "Execution timeout: Program took too long to run"
    except FileNotFoundError as e:
        if "g++" in str(e):
            return "Error: C++ compiler (g++) not found. Please install MinGW or another C++ compiler."
        elif "python" in str(e) or "py" in str(e):
            return "Error: Python interpreter not found. Please install Python and ensure it's in your PATH."
        elif "javac" in str(e) or "java" in str(e):
            return "Error: Java compiler or runtime not found. Please check your JDK installation at C:\\Program Files\\Java\\jdk-24\\bin"
        else:
            return f"Error: Required program not found - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        # Clean up temporary files
        try:
            if code_file_path.exists():
                code_file_path.unlink()
            if input_file_path.exists():
                input_file_path.unlink()
            if output_file_path.exists():
                output_file_path.unlink()
            if language == "cpp" and executable_path.exists():
                executable_path.unlink()
            if language == "java":
                # Clean up Java files
                class_name = "Main"
                if "class" in code and "public class" in code:
                    lines = code.split('\n')
                    for line in lines:
                        if line.strip().startswith('public class'):
                            class_name = line.strip().split('public class')[1].split()[0].strip()
                            break
                java_file_path = codes_dir / f"{class_name}.java"
                class_file_path = codes_dir / f"{class_name}.class"
                if java_file_path.exists():
                    java_file_path.unlink()
                if class_file_path.exists():
                    class_file_path.unlink()
        except:
            pass  # Ignore cleanup errors
