from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import random
import os
from subprocess import run, PIPE

index_page = None
with open("./templates/Index.html", "r") as page:
    index_page = page.read()


def index(request):
    return HttpResponse(index_page)


@csrf_exempt
def run_tm(request):
    TM_info = json.loads(request.body.decode('utf8'))
    session_id = str(random.randint(0, 10000000))
    prog_name = "./binaries/tm_prog" + session_id
    with open(prog_name, "w") as tm_prog:
        tm_prog.write(TM_info["program"])
    p = None
    if TM_info["type"] == "TM":
        p = run(["./binaries/turing_machine", prog_name], stdout=PIPE, input=TM_info["tape"], encoding="ascii", stderr=PIPE)
    elif TM_info["type"] == "Multitape":
        with open("./binaries/tm_tape" + session_id, "w") as tm_prog:
            tm_prog.write(TM_info["program"])
        p = run(["./binaries/multitape", prog_name, "./binaries/tm_tape" + session_id], stdout=PIPE, encoding="ascii", stderr=PIPE)
        os.remove("./binaries/tm_tape" + session_id)
    elif TM_info["type"] == "Nondeterministic":
        with open("./binaries/tm_tape" + session_id, "w") as tm_prog:
            tm_prog.write(TM_info["program"])
        p = run(["./binaries/nondeterministic", prog_name, "./binaries/tm_tape" + session_id], stdout=PIPE, encoding="ascii",
                stderr=PIPE)
        os.remove("./binaries/tm_tape" + session_id)
    elif TM_info["type"] == "High-level":
        os.remove(prog_name)
        return HttpResponse("Not yet implemented")
    os.remove(prog_name)
    if p.returncode != 0:
        return HttpResponse("Returncode: {}\n{}".format(str(p.returncode), p.stderr))
    return HttpResponse(p.stdout)
