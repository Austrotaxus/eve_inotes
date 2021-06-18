import os

from PyInquirer import style_from_dict, prompt

from fetchlib import (
    setup,
    ultimate_decompose,
    output_production_schema,
    prepare_init_table,
)
from fetchlib.utils import (
    SpaceTypes,
    CitadelTypes,
    Rigs,
    BP,
    ProductionClasses,
)


def evaluate_production_for_list():
    questions = [
        {
            "type": "editor",
            "name": "eve_multibuy",
            "message": "Please write what you would like to product",
            "eargs": {"editor": "nano", "ext": ".eve_multibuy"},
        }
    ]

    string = prompt(questions)["eve_multibuy"]
    lines = string.split("\n")
    pairs = []
    for line in lines:
        if line == "":
            continue
        *product, amount = line.split()
        pairs.append((" ".join(product), int(amount)))
    table = prepare_init_table(pairs)
    schema = output_production_schema(table)
    for s in schema:
        print(s)
    return string


def set_lines_amount():
    questions = [
        {
            "type": "input",
            "name": "reac",
            "message": "Reaction amount",
        },
        {
            "type": "input",
            "name": "prod",
            "message": "Production Amount",
        },
    ]

    answers = prompt(questions)
    reac, produc = int(answers["reac"]), int(answers["prod"])
    setup.set_lines_amount(reac, produc)
    return "set_lines_amount"


def add_non_productable():
    question = [
        {"type": "input", "name": "bpc", "message": "Non-productable BPC"}
    ]
    answers = prompt(question)
    setup._non_productables.add(answers["bpc"])
    return "Added non-productable"


def show_setup():
    print("Rigs: ")
    for r in setup.rig_set:
        print(r)
    print("Citadel: {}".format(setup.citadel_type))
    print("Space: {}".format(setup.space_type))
    print(
        "Lines - reaction: {}, production: {}".format(
            setup.reaction_lines, setup.production_lines
        )
    )
    return "Shown setup"


def set_citadel_type():
    current = setup.citadel_type
    possible = CitadelTypes.to_dict().values()
    activity_prompt = {
        "type": "list",
        "name": "citadel",
        "message": "Choose citadel type!"
        "Current citadel type is: {}".format(current),
        "choices": [{"name": name} for name in possible],
    }
    answer = prompt(activity_prompt)
    setup.citadel_type = answer["citadel"]
    return (activity_prompt, answer)


def set_space_type():
    current = setup.space_type
    possible = SpaceTypes.to_dict().values()
    activity_prompt = {
        "type": "list",
        "name": "space",
        "message": "What would you like to do?"
        "Current type is: {}".format(current),
        "choices": [{"name": name} for name in possible],
    }
    answer = prompt(activity_prompt)
    setup.space_type = answer["space"]
    return activity_prompt, answer


def select_rigs():
    current = setup.rig_set
    possible = Rigs.to_dict()
    activity_prompt = {
        "type": "checkbox",
        "name": "rigs",
        "message": "What would you like to do?"
        "Current type is: {}".format(current),
        "choices": [
            {"name": name, "checked": value in current}
            for name, value in possible.items()
        ],
    }
    answer = prompt(activity_prompt)
    setup.rig_set = [possible[a] for a in answer["rigs"]]
    return (activity_prompt, answer)


def set_blueprint():

    questions = [
        {
            "type": "input",
            "name": "type_name",
            "message": "Type Name",
        },
        {
            "type": "input",
            "name": "te",
            "message": "Time efficiency: (From 0.0 to 0.2)",
            "validate": lambda x: is_float(x)
            and float(x) >= 0.0
            and float(x) <= 0.2,
        },
        {
            "type": "input",
            "name": "me",
            "message": "Material efficienciy: (From 0.0 to 0.1)",
            "validate": lambda x: is_float(x)
            and float(x) >= 0.0
            and float(x) <= 0.1,
        },
        {
            "type": "input",
            "name": "runs",
            "default": "0",
            "message": "Runs: (Leave unfilled for BPO)",
            "validate": lambda x: is_int(x) and int(x) >= 0,
        },
        {
            "type": "list",
            "name": "p_type",
            "message": "Product Type?",
            "choices": [
                {"name": name} for name in ProductionClasses.to_dict().values()
            ],
        },
    ]
    answers = prompt(questions)
    bp = BP(
        name=answers["type_name"],
        me=float(answers["me"]),
        te=float(answers["te"]),
        runs=int(answers["runs"]),
        p_type=answers["p_type"],
    )
    setup.add_to_collection([bp])
    return (questions, answers)


def show_collection_blueprint():
    question = {
        "type": "input",
        "name": "bpc_name",
        "message": "Insert BPC name",
    }
    answer = prompt(question)
    no_bpc_msg = "No such BPC in collection!"
    print(setup.collection.prints.get(answer["bpc_name"], no_bpc_msg))
    return (question, answer)


def evaluate_production_schema():
    questions = [
        {
            "type": "input",
            "name": "product",
            "message": "What would you like to product",
        },
        {
            "type": "input",
            "name": "amount",
            "message": "How many?",
            "validate": lambda x: is_int(x) and int(x) > 0,
        },
    ]
    answers = prompt(questions)

    product, amount = answers["product"].title(), int(answers["amount"])
    table = prepare_init_table([(product, amount)])
    strings = output_production_schema(table)
    for s in strings:
        print(s)
    return answers


def calculate_materials():
    pass


def exit_app():
    pass


def main():
    print("Welcome to Eve Inotes!")
    choose_activity_cycle()


def save_and_exit():
    setup.save_setup()
    return None


def activity_set():
    return {
        "Add non-productable": add_non_productable,
        "Calculate materials": calculate_materials,
        "Choose citadel type": set_citadel_type,
        "Choose space type": set_space_type,
        "Evaluate production for list": evaluate_production_for_list,
        "Evaluate production schema": evaluate_production_schema,
        "Select rig set": select_rigs,
        "Set blueprint": set_blueprint,
        "Set lines amount": set_lines_amount,
        "Show blueprint": show_collection_blueprint,
        "Show setup": show_setup,
        "Save and exit": save_and_exit,
    }


# Main application loop
def choose_activity_cycle():
    answer = {}
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        d = activity_set()
        activity_prompt = {
            "type": "list",
            "name": "activity",
            "message": "What would you like to do?",
            "choices": [{"name": name} for name in d.keys()],
        }
        answer = prompt(activity_prompt)

        result = d[answer["activity"]]()
        if not result:
            break
        input()


def is_float(arg):
    try:
        float(arg)
    except Exception:
        return False
    return True


def is_int(arg):
    try:
        int(arg)
    except Exception:
        return False
    return True


if __name__ == "__main__":
    main()
