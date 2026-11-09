"""Explicit generation termination metadata; never infer correctness from stopping."""
def termination_status(tail, eos_ids, cap, elapsed, remaining):
    if tail and tail[-1] in eos_ids:
        return 'OK', 'EOS'
    if len(tail)>=cap:
        return 'OUTPUT_LIMIT', 'TOKEN_LIMIT'
    if elapsed>=remaining:
        return 'WALL_BUDGET', 'TIME_LIMIT'
    return 'UNEXPECTED_STOP', 'NO_EOS'
