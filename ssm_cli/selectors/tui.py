import inquirer

def select(instances: list) -> dict:
    questions = [
        inquirer.List(
            "host",
            message="Which host?",
            choices=instances,
        ),
    ]
    answers = inquirer.prompt(questions)
    if answers is None:
        return None
    return answers["host"]
