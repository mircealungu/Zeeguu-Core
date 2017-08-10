import time


def time_this(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        fname = func.__name__

        elapsed_time = (time.time() - start) * 1000
        print(fname + ' ran for ' + "{0:.2f}".format(elapsed_time) + 'ms')

    return wrapper
