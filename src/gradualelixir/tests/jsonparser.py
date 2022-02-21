import subprocess


def parse(code):
    proc = subprocess.Popen(["..../elixir_port", code])
    outs, errs = proc.communicate()
    return outs, errs
