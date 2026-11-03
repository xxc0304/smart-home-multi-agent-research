"""Fixed example-bank receiver adaptation. No training, retrieval, or transport."""
import copy
import json
import local_judgment_frontend as io
import local_reconstruction_probe as previous
import minimal_final_answer_contract as terminal

METHODS=('no_examples','positive_examples','contrastive_examples')
CAP=1536


def request(case,method,examples):
    if method not in METHODS:raise ValueError('unknown method')
    packet=copy.deepcopy(case['packet'])
    if method!='no_examples':
        packet['worked_examples']=copy.deepcopy(examples[method])
    instructions=(previous.FINAL_INSTRUCTIONS+
        'If worked_examples are present, they are fictional demonstrations, not facts or additional rules '
        'about the current task. Use only transferable reasoning; validate applicability to current evidence. '
        'Do not copy an example choice, entity, threshold or source reliability into this task. '
        'An explicitly labelled incorrect_application in an example is an error illustration, not advice. ')
    return dict(instructions=instructions+'\nPACKET='+json.dumps(packet,ensure_ascii=False),
                schema=terminal.schema(packet),max_output_tokens=CAP)


def packet(req):return io.strict_json(req['instructions'].split('\nPACKET=',1)[1])
