import argparse
import os

import json
import requests
import tqdm

from add_agent_for_evaluation import add_new_agent_rollouts

EXPECTED_BASELINE_AGENT_NAMES = [
    "yamato.kataoka",
    "corianas",
    "TheRealMiners",
    "pm",
    "JustATry",
    "KAIROS",
    "Li_and_Ivan",
    "voggite",
    "KABasalt",
    "Dopamind",
    "GoUp",
    "UniTeam",
    "Miner007",
    "Human1",
    "Human2",
    "Random",
    "BC-Baseline",
]

HUMAN_EVALUATION_INTERFACE_URL = "http://localhost:8000"


parser = argparse.ArgumentParser(description="Initialize a fresh evaluation database by ")
parser.add_argument("--path_to_baseline_answers", type=str, required=True, help="Path to the 'updated_human_answers.json' file from the Evaluation Dataset.")
parser.add_argument("--path_to_banned_workers_json", type=str, required=True, help="Path to the 'banned_workers.json' file from the Evaluation Dataset.")
parser.add_argument("--all_rollouts_dir", type=str, required=True, help="Path to the directory containing the baseline solution videos (e.g., `BC-baseline`, `Human1`, etc.)")

def get_headers():
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": HUMAN_EVALUATION_INTERFACE_URL,
    }
    return headers

def add_baseline_agent_rollouts(all_rollouts_dir):
    """Directory should contain all the baseline submissions, each in a directory named after the agent."""
    for agent_name in tqdm.tqdm(EXPECTED_BASELINE_AGENT_NAMES, desc="Adding baseline agent rollouts to the database"):
        agent_rollouts_dir = os.path.join(all_rollouts_dir, agent_name)
        if not os.path.isdir(agent_rollouts_dir):
            raise ValueError(f"Expected directory {agent_rollouts_dir} does not exist. Make sure all baseline submission agents are present in the directory {all_rollouts_dir}.")
        add_new_agent_rollouts(agent_name, agent_rollouts_dir)

def add_baseline_matches_to_the_database(path_to_baseline_answers):
    with open(path_to_baseline_answers, "r") as f:
        baseline_answers = json.load(f)
    with open(args.path_to_banned_workers_json, "r") as f:
        banned_workers = json.load(f)
    banned_worker_ids = [x["workerId"] for x in banned_workers]
    # Filter out less-than-ideal answers
    baseline_answers = list(filter(lambda x: x["worker_id"] not in banned_worker_ids, baseline_answers))

    # Sort as the json has them in descending order
    finalist_matches = baseline_answers[::-1]

    for match in tqdm.tqdm(finalist_matches, desc="Adding baseline matches to the database"):
        # First create the match
        request_params = {
            "task": match["task"],
            "agent1": match["episodes"][0]["agent_name"],
            "agent2": match["episodes"][1]["agent_name"],
            "seed": match["episodes"][0]["seed"],
        }
        response = requests.post(
            HUMAN_EVALUATION_INTERFACE_URL + "/match/add-match",
            params=request_params,
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to create match: {response.text}")
        response = response.json()

        match_hash = response["hash"]
        episode1_hash = response["episodes"][0]["hash"]
        episode2_hash = response["episodes"][1]["hash"]
        is_draw = match["result"]["is_draw"]
        eval_metadata = match["result"]["eval_metadata"]

        # Order the episodes by the result from recorded hash
        win_player = eval_metadata["win_player"]
        if win_player == "p1" or is_draw:
            ranks = [episode1_hash, episode2_hash]
        else:
            ranks = [episode2_hash, episode1_hash]

        # Update the match info
        headers = get_headers()
        request_data = {
            "hash": match_hash,
            "ranks": ranks,
            "is_draw": is_draw,
            "eval_metadata": json.dumps(eval_metadata),
        }
        response = requests.post(
            HUMAN_EVALUATION_INTERFACE_URL + "/match",
            headers=headers,
            json=request_data,
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to update match: {response.text}")


def main(args):
    # Add the baseline agents to the new database.
    add_baseline_agent_rollouts(args.all_rollouts_dir)

    # Read the baseline answers and add them to the database.
    add_baseline_matches_to_the_database(args.path_to_baseline_answers)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
