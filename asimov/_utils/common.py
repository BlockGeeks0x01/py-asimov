import collections


def dict_add(*args) -> dict:
    total = collections.defaultdict(int)
    for arg in args:
        for key, value in arg.items():
            total[key] += value
    return total
