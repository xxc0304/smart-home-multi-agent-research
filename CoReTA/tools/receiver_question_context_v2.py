"""Future handoff clarification only; NOT enabled in any frozen experiment."""
import copy

QUESTION_CONTEXT_GUIDANCE = (
    'prior_local_question records a question addressed to addressed_member at an earlier stage. '
    'Words such as "you" and "your sources" inside that question refer to addressed_member, '
    'not to the current receiver. The current task is still to decide using all evidence actually '
    'provided in this receiver packet. A question\'s addressee does not restrict the receiver to '
    'that member\'s originals or certify any finding as true. '
)


def contextualize(packet, *, question_author):
    if not isinstance(question_author,str) or not question_author:
        raise ValueError('explicit original question addressee required')
    if 'prior_local_question' in packet:
        raise ValueError('question already contextualized')
    question=packet.get('local_question')
    if not isinstance(question,str) or not question.strip():
        raise ValueError('original local question must be nonempty text')
    if packet.get('local_reconstruction',{}).get('author')!=question_author:
        raise ValueError('this adapter only supports a question answered by its original addressee')
    result=copy.deepcopy(packet)
    result['prior_local_question']=dict(addressed_member=question_author,text=result.pop('local_question'))
    return result


def restore(packet):
    result=copy.deepcopy(packet)
    old=result.pop('prior_local_question')
    if 'local_question' in result:
        raise ValueError('ambiguous duplicate question views')
    result['local_question']=old['text']
    return result
