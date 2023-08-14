import argparse
import os
import random

from imitation.algorithms import bc
from imitation.util.logger import configure as configure_logger

from basalt.utils.embedded_data_loading import load_data_for_imitation_from_path
from basalt.utils.policies import build_n_layer_mlp_policy
from basalt.utils.train_utils import create_on_epoch_end_checkpoint_saver

def add_experiment_specific_args(parser):
    parser.add_argument("--embeddings_dir", type=str, required=True, help="Path to the directory that contains the data embeddings")
    parser.add_argument("--output_dir", type=str, required=True, help="Where to store the experiment results")

    parser.add_argument("--max_files_to_load", type=int, default=None, help="Maximum number of embedding files to load. Takes the first ones.")
    parser.add_argument("--downsampling", type=int, default=1, help="Stride for loading a samples from a file (e.g. 2 -> take every other sample).")
    parser.add_argument("--skip_noops", action="store_true", help="If given, ignore actions that are no-ops.")
    parser.add_argument("--n_epochs", type=int, default=100, help="number of epochs to train for")
    parser.add_argument("--batch_size", type=int, default=1024, help="batch size for training")

    parser.add_argument("--learning_rate", type=float, default=1e-4, help="learning rate for training")
    parser.add_argument("--l2_weight", type=float, default=1e-5, help="L2 loss weight for training")
    parser.add_argument("--entropy_weight", type=float, default=1e-3, help="Entropy weight")

    parser.add_argument("--n_layers", type=int, default=2, help="Number of layers in the MLP")

    parser.add_argument("--embedding_dim", type=int, default=None, help="Embedding dimension for the data embeddings")

    parser.add_argument("--skip_if_exists", action="store_true", help="If set, will not train if the output directory already exists")

    parser.add_argument("--save_every_epochs", type=int, default=1, help="Save the model every n epochs")
    parser.add_argument("--log_every_batches", type=int, default=500, help="How often should we log metrics (in batches)")

    parser.add_argument("--seed", type=int, default=random.randint(0, 1000000), help="Random seed to use")

def main(args):
    # If training dir already exists and flag is set, do not train
    if os.path.exists(args.output_dir) and args.skip_if_exists:
        print(f"Output directory {args.output_dir} already exists. Skipping training.")
        return

    transitions, observation_space, action_space = load_data_for_imitation_from_path(
        args.embeddings_dir,
        args.embedding_dim,
        max_files_to_load=args.max_files_to_load,
        downsampling=args.downsampling,
        skip_noops=args.skip_noops
    )

    embedding_dim = transitions.obs.shape[1]
    policy = build_n_layer_mlp_policy(observation_space, action_space, hidden_dim=embedding_dim, n_layers=args.n_layers)

    os.makedirs(args.output_dir, exist_ok=True)
    logger = configure_logger(args.output_dir, ["stdout", "log", "csv"])

    bc_agent = bc.BC(
        observation_space=observation_space,
        action_space=action_space,
        demonstrations=transitions,
        policy=policy,
        batch_size=args.batch_size,
        l2_weight=args.l2_weight,
        ent_weight=args.entropy_weight,
        rng=args.seed,
        custom_logger=logger,
    )

    checkpoint_saver = create_on_epoch_end_checkpoint_saver(args.output_dir, args.save_every_epochs, bc_agent)
    bc_agent.train(
        n_epochs=args.n_epochs,
        log_interval=args.log_every_batches,
        on_epoch_end=checkpoint_saver,
    )

    # Save final policy
    bc_agent.save_policy(os.path.join(args.output_dir, "policy_final"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Train a BC agent on VPT embeddings for the BASALT Benchmark")
    add_experiment_specific_args(parser)
    args = parser.parse_args()
    main(args)