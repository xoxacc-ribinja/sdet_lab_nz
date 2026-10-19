import copy
import subprocess
import sys


def inspect_sut(mode):
    try:
        result = subprocess.run(
        [sys.executable, "sut/sample_app.py", mode],
        capture_output=True,
        text=True,
        check=False,
        timeout=1,
    )

    except subprocess.TimeoutExpired:
        return 'TIMEOUT'

    return result


def check_sut(mode, result):
    if result == 'TIMEOUT':
        return mode == 'slow'
    elif mode == 'ok':
        if result.stdout.strip() == 'RESULT: OK' and result.stderr == '' and result.returncode == 0:
            return True
    elif mode == 'fail':
        if result.stdout == '' and result.stderr.strip() == 'ERROR: simulated failure' and result.returncode == 17:
            return True
    return False


def mutual_run(mode):
    result = inspect_sut(mode)
    positive_scenario = check_sut(mode, result)
    if mode != 'slow':
        fake_result = copy.copy(result)
        fake_result.stderr = fake_result.stdout
        negative_scenario = check_sut(mode, fake_result)
    else:
        negative_scenario = check_sut(mode, inspect_sut('ok'))
    return positive_scenario, negative_scenario
