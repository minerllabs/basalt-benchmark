#!/bin/bash
# Usage: bash embed_trajectories.sh <basalt_data_dir>
# Embed all of the data with different models
# Will create output structure like:
# <output_dir>
#  <model_name>
#    <env_name>
#      <trajectory_name>.npz
#      <trajectory_name>.npz
#      ...
#    <env_name>
#      <trajectory_name>.npz
#      <trajectory_name>.npz
#      ...
#  <model_name>
#     ...
set -e
# Check arguments
if [ $# -ne 1 ]; then
    echo "Usage: embed_trajectories.sh <basalt_data_dir>"
    exit 1
fi

# Check that ./basalt/embed_trajectories.py exists
if [ ! -f basalt/embed_trajectories.py ]; then
    echo "Could not find basalt/embed_trajectories.py. This script should be run from the root of the repository (i.e., where README.md is)."
    exit 1
fi

ENVS="MineRLBasaltFindCave-v0 MineRLBasaltMakeWaterfall-v0 MineRLBasaltCreateVillageAnimalPen-v0 MineRLBasaltBuildVillageHouse-v0"
declare -A MODEL_WEIGHTS_TO_MODEL
MODEL_WEIGHTS_TO_MODEL=(
    ["foundation-model-1x.weights"]="foundation-model-1x.model"
    ["foundation-model-2x.weights"]="foundation-model-2x.model"
    ["foundation-model-3x.weights"]="foundation-model-3x.model"
    ["rl-from-early-game-2x.weights"]="foundation-model-2x.model"
)

MODEL_WEIGHTS="foundation-model-1x.weights"

BASALT_DATA_DIR=$1
OUTPUT_DIR=$1/embeddings

# Loop over all models and environments.
# For models, get the index of the model name and use that to get the corresponding weights file.
for model_weight_file in $MODEL_WEIGHTS; do
    model_model_file="${MODEL_WEIGHTS_TO_MODEL[$model_weight_file]}"
    model_weight_path=$BASALT_DATA_DIR/VPT-models/$model_weight_file
    model_model_path=$BASALT_DATA_DIR/VPT-models/$model_model_file
    for env in $ENVS; do
        echo "Embedding $env with $model_weight_file"
        this_output_dir=$OUTPUT_DIR/$model_weight_file/$env
        mkdir -p $this_output_dir
        python basalt/embed_trajectories.py \
            --data-dir $BASALT_DATA_DIR/demonstrations/$env \
            --out-dir $this_output_dir \
            --in-model $model_model_path \
            --in-weights $model_weight_path
    done
done
