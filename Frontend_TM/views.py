from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import random
import os
from subprocess import run, PIPE

# save index page globally
# prevents loading the same file from disk multiple times
index_page = None
with open("./templates/Index.html", "r") as page:
    index_page = page.read()


# serve the index page
def index(request):
    return HttpResponse(index_page)


def create_file(filename, content):
    with open(filename, "w") as file:
        file.write(content)


def remove_file(filename):
    os.remove(filename)


def handle_makros(program_string, session_id):
    file_name = "./binaries/makro_file" + session_id
    result_file = "./binaries/makro_file_result" + session_id
    create_file(file_name, program_string)
    p = run(["./binaries/makro_compiler", file_name, result_file], stdout=PIPE, encoding="ascii", stderr=PIPE)
    remove_file(file_name)
    if p.returncode != 0:
        print("Wrong return code !!!!")
        remove_file(result_file)
        return "Returncode: {}\n{}".format(str(p.returncode), p.stderr)
    result = None
    with open(result_file, "r") as file:
        result = file.read()
    remove_file(result_file)
    return result


def handle_tm(request_dict, session_id):
    program_string = None
    if request_dict.get("makro") == "true":
        program_string = handle_makros(request_dict["program"], session_id)
        if program_string.startswith("Returncode:"):
            return program_string
    else:
        program_string = request_dict["program"]
    program_file = "./binaries/tm_prog" + session_id
    tape_file = "./binaries/tm_tape" + session_id
    create_file(program_file, program_string)
    create_file(tape_file, request_dict["tape"])
    p = run(["./binaries/turing_machine", program_file], stdout=PIPE, input=request_dict["tape"], encoding="ascii", stderr=PIPE)
    remove_file(program_file)
    remove_file(tape_file)
    return {
        "Returncode": p.returncode,
        "Output": p.stdout,
        "Error": p.stderr,
        "Tape": None
    }


def handle_multitape_tm(request_dict, session_id):
    program_file = "./binaries/multitape_tm_prog" + session_id
    tape_file = "./binaries/multitape_tm_tape" + session_id
    create_file(program_file, request_dict["program"])
    create_file(tape_file, request_dict["tape"])
    p = run(["./binaries/multitape_tm", "-v", program_file, tape_file], stdout=PIPE, encoding="ascii", stderr=PIPE)
    remove_file(program_file)
    remove_file(tape_file)
    return {
        "Returncode": p.returncode,
        "Output": p.stdout,
        "Error": p.stderr,
        "Tape": None
    }


def handle_multitape_compiler(request_dict, session_id):
    program_file = "./binaries/multitape_tm_prog" + session_id
    tape_file = "./binaries/multitape_tm_tape" + session_id
    create_file(program_file, request_dict["program"])
    create_file(tape_file, request_dict["tape"])
    p = run(["./binaries/multitape_tm", tape_file, program_file], stdout=PIPE, encoding="ascii", stderr=PIPE)
    remove_file(program_file)
    remove_file(tape_file)
    return {
        "Returncode": p.returncode,
        "Output": p.stdout,
        "Error": p.stderr,
        "Tape": None
    }


def handle_nondeterministic_tm(request_dict, session_id):
    program_string = None
    if request_dict.get("makro"):
        program_string = handle_makros(request_dict["program"], session_id)
        if program_string.startswith("Returncode:"):
            return program_string
    else:
        program_string = request_dict["program"]
    program_file = "./binaries/nondeterministic_tm_prog" + session_id
    create_file(program_file, program_string)
    p = run(["./binaries/nondeterministic_tm", "-v", program_file], stdout=PIPE, encoding="ascii", stderr=PIPE)
    remove_file(program_file)
    return {
        "Returncode": p.returncode,
        "Output": p.stdout,
        "Error": p.stderr,
        "Tape": None
    }


def handle_high_level_tm(request_dict, session_id):
    program_file = "./binaries/nondeterministic_tm_prog" + session_id
    output_file = "./binaries/nondeterministic_tm_out" + session_id
    create_file(program_file, request_dict["program"])
    p = run(["./binaries/high_level_compiler", "-v", program_file, output_file], stdout=PIPE, encoding="ascii", stderr=PIPE)
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
