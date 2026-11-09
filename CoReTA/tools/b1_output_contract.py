"""Explicit concise output contract; no answer extraction or semantic judging."""
VERSION = 'B1_CONCISE_V4'
READABLE_VERSION = 'B1_CONCISE_READABLE_V5'
LONG_WORK_VERSION = 'B1_LONG_WORK1024_V6'
ANSWER = ('Output ONLY one answer entity: a name, date, number, or short phrase. Maximum 12 words. '
          'No biography or explanation. If the answer is unavailable, output Unknown.')
WORK = ('Write at most 120 words. Focus on relevant supplied evidence and your current conclusion. '
        'Do not walk through every paragraph or repeat points. Finish even if uncertain.')


def instruction(stage):
    return WORK if stage == 'work' else ANSWER


def violation(text, stage):
    if not isinstance(text, str) or not text.strip():
        return 'EMPTY_OR_NON_TEXT'
    if len(text.split()) > (120 if stage == 'work' else 12):
        return 'WORD_LIMIT'
    if stage != 'work' and len(text.strip().splitlines()) != 1:
        return 'MULTILINE_ANSWER'
    return None
