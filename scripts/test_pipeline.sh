#!/bin/bash
# Run through whole setup, training and rollout pipeline with quick settings to test that everything works
# This does following steps:
#  - Download max 4GB of demonstration data (+ 1GB for the VPT models)
#  - Embed the data
#  - Train models with only few epochs
#  - Rollout models on MineRLBasalt* environments for only few seconds to produce short videos
# If everything is succesful, you should see the videos in the `pipeline_test_data/rollouts` directory.
set -e

# Check that we are in the root of the repository
if [ ! -d "scripts" ]; then
    echo "This script should be run from the root of the repository with 'bash ./scripts/test_pipeline.sh'"
    exit 1
fi

# Download limited amount of demonstration data
bash ./scripts/download_demonstration_data.sh pipeline_test_data 1000

# Embed the data
bash ./scripts/embed_trajectories.sh pipeline_test_data

# Train models with only five epochs
bash ./scripts/train_bc.sh pipeline_test_data 5

# Rollout models on MineRLBasalt* environments for only 5 seconds to produce short videos
# Each second is 20 steps
bash ./scripts/rollout_bc.sh pipeline_test_data 100