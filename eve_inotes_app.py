from PyInquirer import style_from_dict, prompt

from fetchlib import setup, ultimate_decompose, output_production_chema
from fetchlib.utils import SpaceTypes, CitadelTypes


def change_setup():
    pass


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


def add_rig():
    pass


def remove_rig():
    pass


def set_bpc_params():
    pass


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


def calculate_materials():
    pass


def exit_app():
    pass


def main():
    print("Welcome to Eve Inotes!")
    choose_activity_cycle()


def activity_set():
    return {
        "Calculate materals": calculate_materials,
        "Evaluate production schema": evaluate_production_schema,
        "Choose space type": set_space_type,
        "Choose citadel type": set_citadel_type,
        "Exit!": None,
    }


def choose_activity_cycle():
    answer = {}
    while True:
        d = activity_set()
        activity_prompt = {
            "type": "list",
            "name": "activity",
            "message": "What would you like to do?",
            # 'choices': list(d.items())
            "choices": [{"name": name} for name in d.keys()],
        }
        answer = prompt(activity_prompt)

        if not d[answer["activity"]]:
            setup.save_setup()
            break

        d[answer["activity"]]()


if __name__ == "__main__":
    main()
