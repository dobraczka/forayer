"""Help with randomn functions."""
import random
from typing import Union


def random_generator(seed: Union[int, random.Random] = None) -> random.Random:
    """Create or return random generator.

    Parameters
    ----------
    seed : Union[int, random.Random]
        Either a random generator or a seed or None.
    Returns
    -------
    random.Random
        If None was provided return a randomly seeded
        random generator. If a seed was provideded return
        a generator with this seed. If a random.Random object
        was provided return it.
    """
    if seed is not None:
        if isinstance(seed, int):
            r_gen = random.Random(seed)
        elif isinstance(seed, random.Random):
            r_gen = seed
    else:
        r_gen = random.Random(seed)
    return r_gen
