import argparse
import os
import json

import numpy as np
import torch as th
import gym
import minerl
import tqdm
from minerl.herobraine.env_specs.basalt_specs import BasaltBaseEnvSpec, FindCaveEnvSpec, MakeWaterfallEnvSpec, PenAnimalsVillageEnvSpec, VillageMakeHouseEnvSpec
from minerl.herobraine.hero.mc import ALL_ITEMS
from minerl.herobraine.hero import handlers
from imitation.algorithms import bc
import videoio

from basalt.embed_trajectories import load_model_parameters
from basalt.vpt_lib.agent import MineRLAgent

IMAGE_RESOLUTION = (640, 360)
# Manual mapping so that below patching works
ENV_NAME_TO_SPEC = {
    "MineRLBasaltFindCave-v0": FindCaveEnvSpec,
    "MineRLBasaltMakeWaterfall-v0": MakeWaterfallEnvSpec,
    "MineRLBasaltCreateVillageAnimalPen-v0": PenAnimalsVillageEnvSpec,
    "MineRLBasaltBuildVillageHouse-v0": VillageMakeHouseEnvSpec,
}

# These are the seeds per environment models were evaluated on
ENV_TO_BASALT_2022_SEEDS = {
    "MineRLBasaltFindCave-v0": [14169, 65101, 78472, 76379, 39802, 95099, 63686, 49077, 77533, 31703, 73365],
    "MineRLBasaltMakeWaterfall-v0": [95674, 39036, 70373, 84685, 91255, 56595, 53737, 12095, 86455, 19570, 40250],
    "MineRLBasaltCreateVillageAnimalPen-v0": [21212, 85236, 14975, 57764, 56029, 65215, 83805, 35884, 27406, 5681265, 20848],
    "MineRLBasaltBuildVillageHouse-v0": [52216, 29342, 67640, 73169, 86898, 70333, 12658, 99066, 92974, 32150, 78702],
}

KEYS_OF_INTEREST = ['equipped_items', 'life_stats', 'location_stats', 'use_item', 'drop', 'pickup', 'break_item', 'craft_item', 'mine_block', 'damage_dealt', 'entity_killed_by', 'kill_entity', 'full_stats']

# Hotpatch the MineRL BASALT envs to report more statistics.
# NOTE: this is only to get more information on what agent is doing.
#       None of this information is passed to the agent.
def new_create_observables(self):
    obs_handler_pov = handlers.POVObservation(self.resolution)
    return [
        obs_handler_pov,
        handlers.EquippedItemObservation(
            items=ALL_ITEMS,
            mainhand=True,
            offhand=True,
            armor=True,
            _default="air",
            _other="air",
        ),
        handlers.ObservationFromLifeStats(),
        handlers.ObservationFromCurrentLocation(),
        handlers.ObserveFromFullStats("use_item"),
        handlers.ObserveFromFullStats("drop"),
        handlers.ObserveFromFullStats("pickup"),
        handlers.ObserveFromFullStats("break_item"),
        handlers.ObserveFromFullStats("craft_item"),
        handlers.ObserveFromFullStats("mine_block"),
        handlers.ObserveFromFullStats("damage_dealt"),
        handlers.ObserveFromFullStats("entity_killed_by"),
        handlers.ObserveFromFullStats("kill_entity"),
        handlers.ObserveFromFullStats(None),
    ]
BasaltBaseEnvSpec.create_observables = new_create_observables

def add_rollout_specific_args(parser):
    parser.add_argument("--output_dir", type=str, required=True, help="Where to store the rollout results")

    parser.add_argument("--agent_type", type=str, default="bc", choices=["bc"], help="Model type.")
    parser.add_argument("--agent_file", type=str, required=True, help="Path to the trained model to rollout")

    parser.add_argument("--vpt_model", required=True, type=str, help="Path to the .model file to be used for embedding")
    parser.add_argument("--vpt_weights", required=True, type=str, help="Path to the .weights file to be used for embedding")

    parser.add_argument("--env", required=True, type=str, choices=ENV_NAME_TO_SPEC.keys(), help="Name of the environment to roll agent in")
    parser.add_argument("--environment_seeds", default=None, nargs="+", type=int, help="Environment seeds to roll out on, one per video.")

    parser.add_argument("--max_steps_per_seed", default=None, type=int, help="Maximum number of steps to run for per seed")

def remove_numpyness_and_remove_zeros(dict_with_numpy_arrays):
    # Recursively remove numpyness from a dictionary.
    # Remove zeros from the dictionary as well to save space.
    if isinstance(dict_with_numpy_arrays, dict):
        new_dict = {}
        for key, value in dict_with_numpy_arrays.items():
            new_value = remove_numpyness_and_remove_zeros(value)
            if new_value != 0:
                new_dict[key] = new_value
        return new_dict
    elif isinstance(dict_with_numpy_arrays, np.ndarray):
        if dict_with_numpy_arrays.size == 1:
            return dict_with_numpy_arrays.item()
        else:
            return dict_with_numpy_arrays.tolist()

def create_json_entry_dict(obs, action):
    stats = {}
    for key in KEYS_OF_INTEREST:
        stats[key] = remove_numpyness_and_remove_zeros(obs[key])
    stats["action"] = remove_numpyness_and_remove_zeros(action)
    stats = json.dumps(stats)
    return stats

def main(args):
    vpt_agent_policy_kwargs, vpt_agent_pi_head_kwargs = load_model_parameters(args.vpt_model)

    vpt_agent = MineRLAgent(policy_kwargs=vpt_agent_policy_kwargs, pi_head_kwargs=vpt_agent_pi_head_kwargs)
    vpt_agent.load_weights(args.vpt_weights)
    vpt_agent.policy.eval()

    dummy_first = th.from_numpy(np.array((False,))).cuda()

    agent = None
    if args.agent_type == "bc":
        agent = bc.reconstruct_policy(args.agent_file)

    env = ENV_NAME_TO_SPEC[args.env]().make()
    # Patch so that we get more statistics
    print("[NOTE] Move symbolic info stuff to MineRL")
    env.create_observables = new_create_observables

    environment_seeds = args.environment_seeds
    if environment_seeds is None:
        environment_seeds = ENV_TO_BASALT_2022_SEEDS[args.env]

    os.makedirs(args.output_dir, exist_ok=True)

    # Reset env extra time to ensure that the first setting will work fine
    env.reset()

    for seed in tqdm.tqdm(environment_seeds, desc="Seeds", leave=False):
        env.seed(seed)
        obs = env.reset()
        hidden_state = vpt_agent.policy.initial_state(1)
        recorder = videoio.VideoWriter(os.path.join(args.output_dir, f"seed_{seed}.mp4"), resolution=(640, 360), fps=20)

        json_data = []
        recorder.write(obs["pov"])

        done = False
        progress_bar = tqdm.tqdm(desc=f"Steps", leave=False)
        step_counter = 0
        while not done:
            # The agent is only allowed to see the "pov" entry of the observation.
            # This function takes the "pov" observation and resizes it for the agent.
            agent_obs = vpt_agent._env_obs_to_agent(obs)
            with th.no_grad():
                vpt_embedding, hidden_state = vpt_agent.policy.get_output_for_observation(
                    agent_obs,
                    hidden_state,
                    dummy_first,
                    return_embedding=True,
                )
                agent_action, _, _ = agent(vpt_embedding[0])
            # We need to have both batch and seq dimensions for the actions
            agent_action_dict = {
                "buttons": agent_action[:, 0].unsqueeze(0),
                "camera": agent_action[:, 1].unsqueeze(0)
            }
            minerl_action = vpt_agent._agent_action_to_env(agent_action_dict)
            minerl_action["ESC"] = agent_action[0, 2].cpu().numpy()

            # Add the symbolic data here so that video and json are in sync
            json_data.append(create_json_entry_dict(obs, minerl_action))

            obs, _, done, _ = env.step(minerl_action)
            recorder.write(obs["pov"])
            progress_bar.update(1)
            step_counter += 1
            if args.max_steps_per_seed is not None and step_counter >= args.max_steps_per_seed:
                break
        recorder.close()

        # Write the jsonl file
        with open(os.path.join(args.output_dir, f"seed_{seed}.jsonl"), "w") as f:
            f.write("\n".join(json_data))

    env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    add_rollout_specific_args(parser)
    args = parser.parse_args()
    main(args)
