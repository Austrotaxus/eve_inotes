import os

from PyInquirer import prompt

from fetchlib import Decomposition, Decompositor, sde, setup, balancify_runs
from fetchlib.utils import CitadelTypes, ProductionClasses, Rigs, SpaceTypes


class InqController:
    def __init__(self, setup):
        self.setup = setup

    def evaluate_production_for_list(self):
        questions = [
            {
                "type": "editor",
                "name": "eve_multibuy",
                "message": "Please write what you would like to product",
                "eargs": {"ext": ".eve_multibuy"},
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

        table = sde.create_init_table(**dict(pairs))
        decompositor = Decompositor(sde, setup)

        decomposition = Decomposition(step=table, decompositor=decompositor)
        print(str(decomposition))
        import pdb

        pdb.set_trace()
        print(balancify_runs(decomposition))
        return string

    def set_lines_amount(self):
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
        self.setup.set_lines_amount(reac, produc)
        return "set_lines_amount"

    def add_non_productable(self):
        question = [
            {
                "type": "input",
                "name": "item",
                "message": "Non-productable item",
            }
        ]
        answers = prompt(question)
        self.setup._non_productables.add(answers["item"])
        return "Added non-productable"

    def show_setup(self):
        print("Rigs: ")
        for r in self.setup.rig_set:
            print(r)
        print("Citadel: {}".format(self.setup.citadel_type))
        print("Space: {}".format(self.setup.space_type))
        print(
            "Lines - reaction: {}, production: {}".format(
                self.setup.reaction_lines, self.setup.production_lines
            )
        )
        return "Shown setup"

    def set_citadel_type(self):
        current = self.setup.citadel_type
        possible = CitadelTypes.to_dict().values()
        activity_prompt = {
            "type": "list",
            "name": "citadel",
            "message": "Choose citadel type!"
            "Current citadel type is: {}".format(current),
            "choices": [{"name": name} for name in possible],
        }
        answer = prompt(activity_prompt)
        self.setup.citadel_type = answer["citadel"]
        return (activity_prompt, answer)

    def set_space_type(self):
        current = self.setup.space_type
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

    def select_rigs(self):
        current = self.setup.rig_set
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
        self.setup.rig_set = [possible[a] for a in answer["rigs"]]
        return (activity_prompt, answer)

    def set_blueprint(self):
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
                    {"name": name}
                    for name in ProductionClasses.to_dict().values()
                ],
            },
        ]
        answers = prompt(questions)
        self.setup.add_blueprint_to_collection(
            name=answers["type_name"],
            material_efficiency=float(answers["me"]),
            time_efficiency=float(answers["te"]),
            runs=int(answers["runs"]),
            product_type=answers["p_type"],
        )
        return (questions, answers)

    def show_collection_blueprint(self):
        question = {
            "type": "input",
            "name": "bpc_name",
            "message": "Insert BPC name",
        }
        answer = prompt(question)
        no_bpc_msg = "No such BPC in collection!"
        print(self.setup.collection.prints.get(answer["bpc_name"], no_bpc_msg))
        return (question, answer)

    def evaluate_production_schema(self):
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
        table = sde.create_init_table(**{product: amount})
        decompositor = Decompositor(sde, setup)

        decomposition = Decomposition(step=table, decompositor=decompositor)
        print(str(decomposition))
        print(balancify_runs(decomposition))
        return answers

    def calculate_materials(self):
        pass

    def exit_app(self):
        pass

    def save_and_exit(self):
        self.setup.save_setup()
        return None

    def activity_set(self):
        return {
            "Add non-productable": self.add_non_productable,
            "Calculate materials": self.calculate_materials,
            "Choose citadel type": self.set_citadel_type,
            "Choose space type": self.set_space_type,
            "Evaluate production for list": self.evaluate_production_for_list,
            "Evaluate production schema": self.evaluate_production_schema,
            "Select rig set": self.select_rigs,
            "Set blueprint": self.set_blueprint,
            "Set lines amount": self.set_lines_amount,
            "Show blueprint": self.show_collection_blueprint,
            "Show setup": self.show_setup,
            "Save and exit": self.save_and_exit,
        }

    # Main application loop
    def choose_activity_cycle(self):
        answer = {}
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            d = self.activity_set()
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
    print("Welcome to Eve Inotes!")
    controller = InqController(setup)
    controller.choose_activity_cycle()
