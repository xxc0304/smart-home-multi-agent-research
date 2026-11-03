"""Matched post-initial call/output ceilings for three/four member experiments."""
from .gateway import defaults


def settings(n, legacy, system):
    if n not in {3,4} or system not in {"initial", "coreta_workboard", "ordinary_discussion", "single"}:
        raise ValueError("Unsupported roster/system")
    result=defaults(n,legacy); caps=result["max_output_tokens"]
    per_cycle=(n-1)*caps["observe"]+sum(caps[k] for k in ("try","check_use","check_effect","choose"))
    total=(n-1)*per_cycle+sum(caps[k] for k in ("finalize","final_check_use","final_check_effect","final_choose"))
    result["limits"].update(max_network_attempts_total=(n if system=="initial" else 1 if system=="single" else (n+1)**2),
        max_output_tokens_total=(n*4096 if system=="initial" else 4096 if system=="single" else total))
    caps["discuss"]=2304
    if system=="ordinary_discussion": caps["finalize"]=total-n*(n+2)*caps["discuss"]
    result["budget_status"]="hiddenbench_development_preparation"
    return result
