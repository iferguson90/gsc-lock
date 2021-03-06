from stats import Stats
import bisect
import random


def loop(args):
    state, transitions, iterations = args
    stats = Stats()

    for t in transitions:
        t.attach_stats_monitor(stats)

    accumulated_rs = _accum([t.rate(state) for t in transitions])
    R = accumulated_rs[-1]

    while not end_conditions_met(state, R, iterations):
        r = random.random() * R
        i = bisect.bisect_left(accumulated_rs, r)

        transitions[i].execute(state, accumulated_rs[i] - r)
        accumulated_rs = _accum([t.rate(state) for t in transitions])
        R = accumulated_rs[-1]

    return stats


def end_conditions_met(state, R, iterations):
    if R == 0:
        return True

    if state.transition_count + 1 > iterations:
        return True
    else:
        return False


def _accum(items):
    result = []
    total = 0
    for i in items:
        total += i
        result.append(total)
    return result
