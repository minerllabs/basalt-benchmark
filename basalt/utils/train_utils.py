import os

def create_on_epoch_end_checkpoint_saver(save_dir, save_every_n_epochs, bc_policy):
    epoch_counter = 0

    def on_epoch_end_callback():
        nonlocal epoch_counter, save_every_n_epochs
        if (epoch_counter % save_every_n_epochs) == 0:
            bc_policy.save_policy(os.path.join(save_dir, f"policy_{epoch_counter}"))
        epoch_counter += 1

    return on_epoch_end_callback