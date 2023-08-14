import argparse
import os

import glob
import shutil
import uuid

import models
from config import Config
from database import engine
from database.session import SessionLocal

parser = argparse.ArgumentParser(description="Add a new agent to the human evaluation database")
parser.add_argument("--agent_name", type=str, required=True, help="Name to give to this agent.")
parser.add_argument("--rollout_dir", type=str, required=True, help="Path to the directory with MineRLBasalt*-v0 directories, each which contain 'seed_[num].mp4' files)")


def get_seed_to_video_path(video_dir, expected_seeds):
    """
    Input should be a directory that is supposed to contain .mp4 videos.

    Check that input is sane, and if data is valid, return seed -> mp4 path dictionary
    """
    seed_to_video_path = {}
    # .mp4 names are in format seed_[num].mp4
    for episode_path in glob.glob(os.path.join(video_dir, "*.mp4")):
        seed = int(os.path.basename(episode_path).split("_")[1].split(".")[0])
        if seed in seed_to_video_path:
            raise ValueError(f"Duplicate seed found: {seed}")
        if seed not in expected_seeds:
            raise ValueError(f"Seed {seed} was not expected for video directory {video_dir}. Check that directory naming is right")
        seed_to_video_path[seed] = episode_path
    return seed_to_video_path


def get_videos_for_rollout_dir(rollout_dir):
    """
    Input should be a directory that is supposed to contain MineRLBasalt*-v0 directories.

    Check that input is sane, and if data is valid, return env -> seed -> mp4 path dictionary
    """
    env_to_seed_to_video_path = {}
    for env_name in Config.BASALT_ENV_NAMES:
        seeds = Config.BASALT_ENV_TO_EXPECTED_SEEDS[env_name]
        env_dir = os.path.join(rollout_dir, env_name)
        if not os.path.isdir(env_dir):
            # Try using the shorter name for the env
            original_attempted_dir = env_dir
            task_name = Config.BASALT_ENV_NAME_TO_TASK[env_name]
            env_dir = os.path.join(rollout_dir, task_name)
            if not os.path.isdir(env_dir):
                raise ValueError(f"Could not find directory {original_attempted_dir} or {env_dir}")
        seed_to_video_path = get_seed_to_video_path(env_dir, Config.BASALT_ENV_TO_EXPECTED_SEEDS[env_name])
        env_to_seed_to_video_path[env_name] = seed_to_video_path
    return env_to_seed_to_video_path

def add_new_agent_rollouts(agent_name, rollout_dir):
    env_to_seed_to_video_path = get_videos_for_rollout_dir(rollout_dir)

    models.Base.metadata.create_all(bind=engine)

    # Instantiate DB
    db = SessionLocal()

    for basalt_env_name, seed_to_video_path in env_to_seed_to_video_path.items():
        task_name = Config.BASALT_ENV_NAME_TO_TASK[basalt_env_name]

        agent = (
            db.query(models.Agent)
            .filter_by(name=agent_name.strip(), task=task_name)
            .first()
        )
        # If the agent already existed, crash. This is to prevent overwriting
        # existing agents.
        if bool(agent):
            raise ValueError(f"Agent {agent_name} already exists for task {task_name}. Remove the agent or use a different name.")

        agent = models.Agent(
            name=agent_name.strip(),
            task=task_name,
            is_approved=True,
        )
        db.add(agent)
        db.commit()

        for seed, original_path in seed_to_video_path.items():
            target_filename = "{}.mp4".format(str(uuid.uuid4()))
            target_filepath = os.path.join(Config.UPLOADS_DIR, target_filename)
            shutil.copy(original_path, target_filepath)

            episode = models.Episode(
                video_filename=target_filename,
                task=task_name,
                seed=str(seed),
            )
            episode.agent = agent
            db.add(episode)
            db.commit()

if __name__ == "__main__":
    args = parser.parse_args()
    add_new_agent_rollouts(args.agent_name, args.rollout_dir)
