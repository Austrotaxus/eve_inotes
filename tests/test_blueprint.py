from fetchlib.blueprint import Blueprint, BlueprintCollection


def test_no_duplicated_names_in_collection():
    first = Blueprint("a", material_efficiency=1, time_efficiency=1, runs=10)
    second = Blueprint("a", material_efficiency=0.9, time_efficiency=0.9, runs=12)
    collection = BlueprintCollection(prints=[])
    collection.add(first)
    collection.add(second)

    assert len(collection) == 1
    assert next(iter(collection)) == second
