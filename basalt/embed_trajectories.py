# Script for embedding original mp4 trajectories with VPT models into .npz files which contain:
#  1. Embeddings
#  2. Button actions (in VPT action space)
#  3. Camera actions (in VPT action space)
#  4. ESC button (binary)
#  5. Is null action (binary)

from argparse import ArgumentParser
import pickle
import time
import os

import torch as th
import numpy as np
import tqdm

from basalt.vpt_lib.agent import MineRLAgent
from basalt.utils.minerl_data_loader import DataLoader
from basalt.vpt_lib.tree_util import tree_map

EPOCHS = 1
BATCH_SIZE = 8
N_WORKERS = 10
DEVICE = "cuda"

REPORT_RATE = 100


def load_model_parameters(path_to_model_file):
    agent_parameters = pickle.load(open(path_to_model_file, "rb"))
    policy_kwargs = agent_parameters["model"]["args"]["net"]["args"]
    pi_head_kwargs = agent_parameters["model"]["args"]["pi_head_opts"]
    pi_head_kwargs["temperature"] = float(pi_head_kwargs["temperature"])
    return policy_kwargs, pi_head_kwargs

def embed_trajectories(data_dir, in_model, in_weights, out_dir, check_accuracies=False):
    agent_policy_kwargs, agent_pi_head_kwargs = load_model_parameters(in_model)

    agent = MineRLAgent(device=DEVICE, policy_kwargs=agent_policy_kwargs, pi_head_kwargs=agent_pi_head_kwargs)
    agent.load_weights(in_weights)
    agent.policy.eval()

    policy = agent.policy

    data_loader = DataLoader(
        dataset_dir=data_dir,
        n_workers=N_WORKERS,
        batch_size=BATCH_SIZE,
        n_epochs=EPOCHS,
        do_not_cut_epoch_tail=True,
    )

    accuracy_metrics = {
        "button_corrects": 0,
        "camera_corrects": 0,
        "total": 0,
    }
    # Keep track of the hidden state per episode/trajectory.
    # DataLoader provides unique id for each episode, which will
    # be different even for the same trajectory when it is loaded
    # up again
    episode_hidden_states = {}
    # Episode id -> [file_name, [embeddings], [button_actions], [camera_actions], [esc_presses], [is_null_action]]]
    episode_embeddings = {}
    dummy_first = th.from_numpy(np.array((False,))).to(DEVICE)

    episode_progress_bar = tqdm.tqdm(desc="Episode", total=len(data_loader.demonstration_tuples))
    batch_progress_bar = tqdm.tqdm(desc="Batch")
    for batch_i, (batch_images, batch_actions, batch_episode_id) in enumerate(data_loader):
        for image, action, episode_id in zip(batch_images, batch_actions, batch_episode_id):
            if image is None and action is None:
                # A work-item was done. Remove hidden state
                if episode_id in episode_hidden_states:
                    removed_hidden_state = episode_hidden_states.pop(episode_id)
                    del removed_hidden_state
                # Save embeddings
                if episode_id in episode_embeddings:
                    episode_id, embeddings, button_actions, camera_actions, esc_actions, is_null_action = episode_embeddings.pop(episode_id)
                    mp4_path = data_loader.get_mp4_path_for_trajectory_id(episode_id)
                    episode_name = os.path.basename(mp4_path).split(".")[0]
                    os.makedirs(out_dir, exist_ok=True)
                    save_path = f"{out_dir}/{episode_name}.npz"
                    np.savez_compressed(
                        save_path,
                        embeddings=np.stack(embeddings, axis=0),
                        button_actions=np.array(button_actions),
                        camera_actions=np.array(camera_actions),
                        esc_actions=np.array(esc_actions),
                        is_null_action=np.array(is_null_action),
                    )
                    episode_progress_bar.update(1)
                continue

            agent_obs = agent._env_obs_to_agent({"pov": image})
            if episode_id not in episode_hidden_states:
                episode_hidden_states[episode_id] = policy.initial_state(1)
            agent_state = episode_hidden_states[episode_id]
            agent_action = agent._env_action_to_agent(action)

            with th.no_grad():
                if check_accuracies:
                    predicted_act, new_agent_state, _ = policy.act(agent_obs, dummy_first, agent_state, stochastic=False)
                    button_prediction = predicted_act["buttons"].item()
                    camera_prediction = predicted_act["camera"].item()
                    true_button = agent_action["buttons"].item()
                    true_camera = agent_action["camera"].item()
                    accuracy_metrics["button_corrects"] += int(button_prediction == true_button)
                    accuracy_metrics["camera_corrects"] += int(camera_prediction == true_camera)
                    accuracy_metrics["total"] += 1
                else:
                    embedding, new_agent_state = policy.get_output_for_observation(
                        agent_obs,
                        agent_state,
                        dummy_first,
                        return_embedding=True,
                    )
                    if episode_id not in episode_embeddings:
                        episode_embeddings[episode_id] = [episode_id, [], [], [], [], []]
                    # Remove time and batch dimensions
                    episode_embeddings[episode_id][1].append(embedding.detach().cpu().numpy().astype(np.float32)[0, 0])
                    episode_embeddings[episode_id][2].append(int(agent_action["buttons"].item()))
                    episode_embeddings[episode_id][3].append(int(agent_action["camera"].item()))
                    episode_embeddings[episode_id][4].append(int(action["ESC"]))
                    episode_embeddings[episode_id][5].append(int(action["is_null_action"]))


            # Make sure we do not try to backprop through sequence
            # (fails with current accumulation)
            new_agent_state = tree_map(lambda x: x.detach(), new_agent_state)
            episode_hidden_states[episode_id] = new_agent_state

        batch_progress_bar.update(1)

        if check_accuracies and (batch_i % REPORT_RATE) == 0:
            tqdm.tqdm.write(f"{batch_i} batches done.")
            tqdm.tqdm.write(f"\tButton accuracy: {accuracy_metrics['button_corrects'] / accuracy_metrics['total']}")
            tqdm.tqdm.write(f"\tCamera accuracy: {accuracy_metrics['camera_corrects'] / accuracy_metrics['total']}")
            accuracy_metrics["button_corrects"] = 0
            accuracy_metrics["camera_corrects"] = 0
            accuracy_metrics["total"] = 0


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--data-dir", type=str, required=True, help="Path to the directory containing recordings to be trained on")
    parser.add_argument("--in-model", required=True, type=str, help="Path to the .model file to be finetuned")
    parser.add_argument("--in-weights", required=True, type=str, help="Path to the .weights file to be finetuned")
    parser.add_argument("--out-dir", required=True, type=str, help="Path where embeddings are stored")
    parser.add_argument("--check-accuracies", action="store_true", help="Instead of saving embeddings, save accuracies")

    args = parser.parse_args()
    embed_trajectories(args.data_dir, args.in_model, args.in_weights, args.out_dir, args.check_accuracies)
