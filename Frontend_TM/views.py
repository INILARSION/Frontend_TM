from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import random
import os
from pathlib import Path
from subprocess import run, PIPE
import logging

# save index page globally
# prevents loading the same file from disk multiple times
index_page = None
base_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
with open(base_path / "templates/Index.html", "r") as page:
    index_page = page.read()

logger = logging.getLogger(__name__)
logger.critical("Starting server at http://127.0.0.1:8000/")


# serve the index page
def index(request):
    return HttpResponse(index_page)


def create_file(filename, content):
    with open(filename, "w") as file:
        file.write(content)


def remove_file(filename):
    os.remove(filename)


def handle_makros(program_string, session_id):
    file_name = str(base_path / "binaries/makro_file") + session_id
    result_file = str(base_path / "binaries/makro_file_result") + session_id
    create_file(file_name, program_string)
    p = run([base_path / "binaries/makro_compiler", file_name, result_file], stdout=PIPE, encoding="ascii", stderr=PIPE)
    remove_file(file_name)
    result = {
        "Returncode": p.returncode,
        "Error": p.stdout,
        "Tape": None
    }
    if p.returncode != 0:
        remove_file(result_file)
        return result
    with open(result_file, "r") as file:
        result["Output"] = file.read()
    remove_file(result_file)
    return result


def handle_tm(request_dict, session_id):
    program_string = None
    if request_dict.get("makro"):
        program = handle_makros(request_dict["program"], session_id)
        if program["Returncode"] != 0:
            return program
        else:
            program_string = program["Output"]
    else:
        program_string = request_dict["program"]
    program_file = str(base_path / "binaries/tm_prog") + session_id
    tape_file = str(base_path / "binaries/tm_tape") + session_id
    create_file(program_file, program_string)
    create_file(tape_file, request_dict["tape"])
    p = run([base_path / "binaries/turing_machine", program_file], stdout=PIPE, input=request_dict["tape"], encoding="ascii", stderr=PIPE)
    remove_file(program_file)
    remove_file(tape_file)
    return {
        "Returncode": p.returncode,
        "Output": p.stdout,
        "Error": p.stdout,
        "Tape": None
    }


def handle_multitape_tm(request_dict, session_id):
    program_file = str(base_path / "binaries/multitape_tm_prog") + session_id
    tape_file = str(base_path / "binaries/multitape_tm_tape") + session_id
    create_file(program_file, request_dict["program"])
    create_file(tape_file, request_dict["tape"])
    p = run([base_path / "binaries/multitape_tm", "-v", program_file, tape_file], stdout=PIPE, encoding="ascii", stderr=PIPE)
    remove_file(program_file)
    remove_file(tape_file)
    return {
        "Returncode": p.returncode,
        "Output": p.stdout,
        "Error": p.stdout,
        "Tape": None
    }


def handle_multitape_compiler(request_dict, session_id):
    program_file = str(base_path / "binaries/multitape_tm_prog") + session_id
    tape_file = str(base_path / "binaries/multitape_tm_tape") + session_id
    create_file(program_file, request_dict["program"])
    create_file(tape_file, request_dict["tape"])
    p = run([base_path / "binaries/multitape_tm", tape_file, program_file], stdout=PIPE, encoding="ascii", stderr=PIPE)
    remove_file(program_file)
    remove_file(tape_file)
    return {
        "Returncode": p.returncode,
        "Output": p.stdout,
        "Error": p.stdout,
        "Tape": None
    }


def handle_nondeterministic_tm(request_dict, session_id):
    program_string = None
    if request_dict.get("makro"):
        program = handle_makros(request_dict["program"], session_id)
        if program["Returncode"] != 0:
            return program
        else:
            program_string = program["Output"]
    else:
        program_string = request_dict["program"]
    program_file = str(base_path / "binaries/nondeterministic_tm_prog") + session_id
    create_file(program_file, program_string)
    p = run([base_path / "binaries/nondeterministic_tm", "-v", program_file], stdout=PIPE, encoding="ascii", stderr=PIPE)
    remove_file(program_file)
    return {
        "Returncode": p.returncode,
        "Output": p.stdout,
        "Error": p.stdout,
        "Tape": None
    }


def handle_high_level_tm(request_dict, session_id):
    program_file = str(base_path / "binaries/nondeterministic_tm_prog") + session_id
    output_file = str(base_path / "binaries/nondeterministic_tm_out") + session_id
    create_file(program_file, request_dict["program"])
    p = run([base_path / "binaries/high_level_compiler", "-v", program_file, output_file], stdout=PIPE, encoding="ascii", stderr=PIPE)
    result = {
        "Returncode": p.returncode,
        "Error": p.stderr,
    }
    with open(output_file + ".delta", "r") as delta_file:
        result["Output"] = delta_file.read()
    with open(output_file + ".tape", "r") as tape_file:
        result["Tape"] = tape_file.read()
    remove_file(program_file)
    remove_file(output_file + ".delta")
    remove_file(output_file + ".tape")
    return result


# handles POST-request with the turing machine data
# uses the helper functions to execute the binaries as a subprocess
@csrf_exempt
def run_tm(request):
    request_dict = json.loads(request.body.decode('utf8'))
    session_id = str(random.randint(0, 10000000))
    response = None
    if request_dict["type"] == "TM":
        response = handle_tm(request_dict, session_id)
    elif request_dict["type"] == "Multitape_Compiler":
        response = handle_multitape_compiler(request_dict, session_id)
    elif request_dict["type"] == "Multitape_TM":
        response = handle_multitape_tm(request_dict, session_id)
    elif request_dict["type"] == "Nondeterministic":
        response = handle_nondeterministic_tm(request_dict, session_id)
    elif request_dict["type"] == "High-level":
        response = handle_high_level_tm(request_dict, session_id)
    response = json.dumps(response)
    return HttpResponse(response)
