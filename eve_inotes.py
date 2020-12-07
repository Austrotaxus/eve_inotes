from PyInquirer import style_from_dict, prompt
from fetchlib import setup, ultimate_decompose, output_production_chema
from fetchlib.utils import (
    SpaceTypes,
    CitadelTypes,
    Rigs,
    BP,
    ProductionClasses,
)
import os


def show_setup():
    print("Rigs: ")
    for r in setup.rig_set:
        print(r)
    print("Citadel: ")
    print(setup.citadel_type)
    print("Space: ")
    print(setup.space_type)
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

    questions = [
        {
            "type": "input",
            "name": "type_name",
            "message": "Type Name",
        },
        {
            "type": "input",
            "name": "te",
            "message": "Time required: (From 0.8 to 1.0)",
            "validate": lambda x: is_float(x)
            and float(x) >= 0.8
            and float(x) <= 1.0,
        },
        {
            "type": "input",
            "name": "me",
            "message": "Materials required? (From 0.9 to 1.0)",
            "validate": lambda x: is_float(x)
            and float(x) >= 0.9
            and float(x) <= 1.0,
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


def add_non_productables():
    pass


def evaluate_production_schema():
    questions = [
        {
            "type": "input",
            "name": "product",
            "message": "What would you like to product",
        },
        {
            "type": "input",
            "name": "runs",
            "message": "How many runs?",
        },
    ]
    answers = prompt(questions)
    output_production_chema(answers["product"], int(answers["runs"]))
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
        "Calculate materals": calculate_materials,
        "Evaluate production schema": evaluate_production_schema,
        "Choose space type": set_space_type,
        "Choose citadel type": set_citadel_type,
        "Select rig set": select_rigs,
        "Show setup": show_setup,
        "Show blueprint": show_collection_blueprint,
        "Set blueprint": set_blueprint,
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


if __name__ == "__main__":
    main()
