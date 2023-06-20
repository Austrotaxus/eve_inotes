import pandas as pd

from fetchlib.blueprint import Blueprint, BlueprintCollection


def test_no_duplicated_names_in_collection():
    first = Blueprint("a", material_efficiency=0, time_efficiency=0, runs=10)
    second = Blueprint("a", material_efficiency=0.1, time_efficiency=0.1, runs=12)
    collection = BlueprintCollection(prints=[])
    collection.add(first)
    collection.add(second)

    assert len(collection) == 1
    assert next(iter(collection)) == second


def test_to_dataframce():
    """Expected dataframe is:
            te_impact  me_impact  runs
    a       0.8        0.9        10

    """
    blueprint = Blueprint("a", material_efficiency=0.1, time_efficiency=0.2, runs=10)
    collection = BlueprintCollection(prints=[blueprint])
    df = collection.to_dataframe
    expected = pd.DataFrame(
        data={"me_impact": [0.9], "te_impact": [0.8], "run": [10]}, index=["a"]
    )
    assert df.equals(expected)
