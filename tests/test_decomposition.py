from unittest.mock import patch

from fetchlib.decomposition import Decomposition


def test_decompositon():
    atomic_sum = 0

    def _final_condition(_, next_step):
        return next_step == 0

    def decompositor(step):
        nonlocal atomic_sum
        atomic, next_step = 1, step - 1
        atomic_sum += atomic
        return atomic, next_step

    with patch.object(Decomposition, "_finalize_condition", _final_condition):
        decomposition = Decomposition(step=10, decompositor=decompositor)

    assert [step for step in iter(decomposition)] == list(range(10, 0, -1))

    assert atomic_sum == 10
