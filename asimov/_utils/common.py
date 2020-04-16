import collections


def dict_add(*args) -> dict:
    total = collections.defaultdict(int)
    for arg in args:
        for k, v in arg.items():
            total[k] += v
    return total
