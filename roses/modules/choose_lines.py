from typing import Dict, List
import json
import random
import os
from utils import read_json_file

def find_lines(emotion: str, rhyming_partials: List[Dict]):
    """
    Creates combinations of ending lines (3rd and 4th) from some knowledgebase.
    """

    data = read_json_file("data/bible_kjv_wrangled.json")

    ret = []
    for partial in rhyming_partials:
        for word in partial['rhymes']:
            third = data[random.choice(list(data))]
            fourth = data[random.choice(list(data))]
            #fourth = f'and you should be {word}'
            new_partial = partial.copy()
            new_partial['rest'] = (third, fourth)
            ret.append(new_partial)
    return ret


# For testing
if __name__ == '__main__':
    example_emotion = 'sad'
    example_rhyming_partials = [{'word_pair': ('animal', 'legged'), 'verb': 'is', 'rhymes': [
        'gielgud', 'rugged', 'ragged', 'begged', 'pegged']}]
    output = find_lines(example_emotion, example_rhyming_partials)
    print(output)
