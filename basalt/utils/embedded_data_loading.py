# Loading embedded trajectories in formats that work for imitation library
# Since imitation does not seem to support dictionaries easily, actions will be MultiDiscrete actions:
#   1. Button actions
#   2. Camera actions
#   3. ESC button
# 1. and 2. follow the original VPT model actiono space, while ESC button is new binary button for predicting
# when to press ESC (to end the episode)

import os
import glob

import numpy as np
from gym import spaces
from imitation.data.types import Transitions
from tqdm import tqdm

from basalt.vpt_lib.agent import AGENT_NUM_BUTTON_ACTIONS, AGENT_NUM_CAMERA_ACTIONS

KEYS_FOR_TRANSITIONS = ["obs", "next_obs", "acts", "dones", "infos"]

# Maximum number of transitions to load. Using a fixed array size avoids expensive recreation of arrays.
# This is hardcoded for `downsampling`=2.
# This is suitable for ~50GB of RAM.
MAX_DATA_SIZE = 4_000_000

def build_obs_and_act_gym_spaces(transitions):
    observation_space = spaces.Box(low=-float("inf"), high=float("inf"), shape=(transitions.obs.shape[1],))
    # 2 is for ESC button
    action_space = spaces.MultiDiscrete([AGENT_NUM_BUTTON_ACTIONS, AGENT_NUM_CAMERA_ACTIONS, 2])
    return observation_space, action_space

def get_all_npz_files_in_dir(dir_path):
    return glob.glob(os.path.join(dir_path, "*.npz"))

def hotfix_flattened_embeddings(embeddings, embedding_dim):
    """Reshape accidentally flattened embeddings back into correct shape"""
    return embeddings.reshape(-1, embedding_dim)

def load_embedded_trajectories_as_transitions(npz_file_paths, progress_bar=False, expected_embedding_dim=None, downsampling=1, skip_noops=False):
    # Create arrays with enough space which we then fill
    obs = np.zeros((MAX_DATA_SIZE, expected_embedding_dim), dtype=np.float32)
    next_obs = np.zeros((MAX_DATA_SIZE, expected_embedding_dim), dtype=np.float32)
    acts = np.zeros((MAX_DATA_SIZE, 3), dtype=np.int32)
    dones = np.zeros((MAX_DATA_SIZE,), dtype=bool)
    infos = np.zeros((MAX_DATA_SIZE,), dtype=object)
    current_index = 0
    for npz_file_path in tqdm(npz_file_paths, desc="Loading trajectories", disable=not progress_bar, leave=False):
        data = np.load(npz_file_path)
        try:
            embeddings = data["embeddings"]
            button_actions = data["button_actions"]
            camera_actions = data["camera_actions"]
            esc_actions = data["esc_actions"]
            is_null_action = data["is_null_action"]
        except KeyError as e:
            print(f"KeyError while loading {npz_file_path}: {e}")
            continue

        if embeddings.ndim == 1:
            assert expected_embedding_dim is not None, "Expected embedding dim must be provided if embeddings are flattened"
            embeddings = hotfix_flattened_embeddings(embeddings, expected_embedding_dim)

        if skip_noops:
            # Remove noops
            valid_action_mask = ~(is_null_action.astype(np.bool))
            embeddings = embeddings[valid_action_mask]
            button_actions = button_actions[valid_action_mask]
            camera_actions = camera_actions[valid_action_mask]
            esc_actions = esc_actions[valid_action_mask]

        # Downsampling
        embeddings = embeddings[::downsampling]
        button_actions = button_actions[::downsampling]
        camera_actions = camera_actions[::downsampling]
        esc_actions = esc_actions[::downsampling]

        assert embeddings.shape[0] == button_actions.shape[0] == camera_actions.shape[0] == esc_actions.shape[0], f"Shapes do not match: {embeddings.shape}, {button_actions.shape}, {camera_actions.shape}"

        # Add to arrays
        n = embeddings.shape[0]
        obs[current_index:current_index + n] = embeddings
        # Pad last observation with zeros
        next_obs[current_index:current_index + n] = np.concatenate((embeddings[1:], np.zeros((1, expected_embedding_dim))), axis=0)
        acts[current_index:current_index + n] = np.stack([button_actions, camera_actions, esc_actions], axis=1)
        dones[current_index + n] = True
        current_index += n

        if current_index >= MAX_DATA_SIZE:
            raise RuntimeError(f"Reached max data size of {MAX_DATA_SIZE} while loading trajectories. Increase `MAX_DATA_SIZE` entry or increase `downsampling` to load less data.")

    # Trim arrays to correct size
    obs = obs[:current_index]
    next_obs = next_obs[:current_index]
    acts = acts[:current_index]
    dones = dones[:current_index]
    infos = infos[:current_index]

    # Create dictionary
    concat_all_parts = dict(zip(KEYS_FOR_TRANSITIONS, [obs, next_obs, acts, dones, infos]))

    print(f"Loaded {len(concat_all_parts['obs'])} transitions")

    return Transitions(**concat_all_parts)

def load_data_for_imitation_from_path(data_path, expected_embedding_dim=None, max_files_to_load=None, downsampling=1, skip_noops=False):
    """
    Load data from a path in a format that can be used by the imitation library.
    Returns:
        transitions: imitation.data.types.Transitions
        observation_space: Observation space matching the observations
        action_space: Action space matching the actions
    """
    filelist = get_all_npz_files_in_dir(data_path)
    if max_files_to_load is not None:
        filelist = filelist[:max_files_to_load]
    transitions = load_embedded_trajectories_as_transitions(filelist, progress_bar=True, expected_embedding_dim=expected_embedding_dim, downsampling=downsampling, skip_noops=skip_noops)
    observation_space, action_space = build_obs_and_act_gym_spaces(transitions)
    return transitions, observation_space, action_space
