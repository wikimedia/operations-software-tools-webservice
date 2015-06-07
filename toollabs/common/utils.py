import sys
import time


def wait_for(predicate, prompt, timeout=15):
    """
    Wait for function predicate to return true, printing ....s until it is true
    or timeout seconds have elapsed.

    Prints prompt before starting

    :param func: Function that returns boolean.
    :param prompt: String to print before starting ...s
    :param timeout: seconds to wait before returning
    :return: True if predicate returned true before timeout, false otherwise
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()
    for i in xrange(timeout):
        if predicate():
            return True
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(1)
    return False
