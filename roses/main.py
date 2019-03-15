"""Group Roses' main file.

Should contain initialize- and create-functions.
"""
import random
import json

DUMMY_POEMS_PATH = "roses/dummy_poems.json"


class PoemCreator:

    def __init__(self, *args, **kwargs):
        """Initialize any data structures, objects, etc. needed by the system so that the system is fully prepared
        when create-function is called.

        Only keyword arguments are supported in config.json
        """
        print("Group Roses initialize.")
        poems = []
        with open(DUMMY_POEMS_PATH) as f:
            s = f.read()
            poems = json.loads(s)
            print(f'poems {poems}')
        self.poems = poems
        self.alphabet = kwargs.pop('alphabet', "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.vocals = kwargs.pop('vocals', "AEIOUY")
        self.word_length = kwargs.pop('word_length', (4, 8))

        # Each creator should have domain specified: title, poetry, music, image, etc.
        self.domain = 'poetry'

    def generate(self, *args, **kwargs):
        """Poem generator.
        """
        poem = random.choice(self.poems)
        return poem

    def evaluate(self, poem):
        """Evaluate poem by counting how many vocals it has.
        """
        e = 0
        for char in poem:
            if char in self.vocals:
                e += 1.0
        return e / len(poem)

    def create(self, emotion, word_pairs, number_of_artifacts=10, **kwargs):
        """Create artifacts in the group's domain.

        The given inputs can be parsed and deciphered by the system using any methods available.

        The function should return a list in the form of:

            [
                (artifact1, {"evaluation": 0.76, 'foo': 'bar'}),
                (artifact2, {"evaluation": 0.89, 'foo': 'baz'}),
                # ...
                (artifactn, {"evaluation": 0.29, 'foo': 'bax'})
            ]

        :param str emotion:
            One of "the six basic emotions": anger, disgust, fear, happiness, sadness or surprise.
            The emotion should be perceivable in the output(s).
        :param list word_pairs:
            List of 2-tuples, the word pairs associated with the output(s). The word_pairs are (noun, property) pairings
            where each pair presents a noun and its property which may be visible in the output. (Think of more creative
            ways to present the pairings than literal meaning.)
        :param int number_of_artifacts:
            Number of artifacts returned
        :returns:
            List with *number_of_artifacts* elements. Each element should be (artifact, metadata) pair, where metadata
            should be a dictionary holding at least 'evaluation' keyword with float value.

        """
        print("Group Roses create with input args: {} {}".format(emotion, word_pairs))
        ret = [(poem, {'evaluation': self.evaluate(poem)}) for poem in [self.generate() for _ in range(number_of_artifacts)]]
        return ret

