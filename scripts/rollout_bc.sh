#!/bin/bash
# Usage: bash rollout_bc.sh <basalt_data_dir> [steps_per_rollout]
# Takes trained BC models and rolls them out on the MineRLBasalt* environments to produce the videos
set -e
if [ $# -lt 1 ]; then
    echo "Usage: rollout_bc.sh <basalt_data_dir> [steps_per_rollout]"
    exit 1
fi

additional_args=""
if [ $# -eq 2 ]; then
    additional_args="--max_steps_per_seed $2"
fi

# Make sure xvfb is installed
if ! [ -x "$(command -v xvfb-run)" ]; then
    echo "Error: xvfb-run command is not available. Install xvfb it with 'sudo apt-get install xvfb'."
    exit 1
fi

envs="MineRLBasaltFindCave-v0 MineRLBasaltMakeWaterfall-v0 MineRLBasaltCreateVillageAnimalPen-v0 MineRLBasaltBuildVillageHouse-v0"
vpt_model="foundation-model-1x.model"
vpt_weights="foundation-model-1x.weights"

models_dir="$1/bc_models"
rollouts_dir="$1/rollouts"
vpt_dir="$1/VPT-models"

models_to_rollout="policy_final"

for env in $envs; do
    for model in $models_to_rollout; do
        models_path=$models_dir/$env/"policy_final"
        output_dir=$rollouts_dir/$env
        mkdir -p $output_dir
        echo "Rolling out $models_path on $env"
        xvfb-run -a python basalt/rollout_model.py \
            --output_dir $output_dir \
            --agent_type "bc" \
            --agent_file $models_path \
            --vpt_model $vpt_dir/$vpt_model \
            --vpt_weights $vpt_dir/$vpt_weights \
            --env $env \
            $additional_args
    done
done
