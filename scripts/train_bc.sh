#!/bin/bash
# Usage: bash train_bc.sh <basalt_data_dir> [n_epochs]
# Trains one BC model per BASALT Benchmark task, using the embeddings from the `embed_trajectories.sh` script.
set -e
if [ $# -lt 1 ]; then
    echo "Usage: train_bc.sh <basalt_data_dir> [n_epochs]"
    exit 1
fi

n_epochs=100
if [ $# -eq 2 ]; then
    n_epochs=$2
fi

envs="MineRLBasaltFindCave-v0 MineRLBasaltMakeWaterfall-v0 MineRLBasaltCreateVillageAnimalPen-v0 MineRLBasaltBuildVillageHouse-v0"
embedding_dim=1024
batch_size=4096
save_every_n_epochs=10
# How many frames between points we take for training
downsampling=2
# Settings of the best training loss by sweeping over different settings
# on x1 widths with FindCave task
lr="1e-5"
l2_weight="0"
entropy_weight="1e-5"
n_layer="3"

embeddings_dir="$1/embeddings/foundation-model-1x.weights"
output_path="$1/bc_models/"

# Check that the embeddings directory exists
if [ ! -d $embeddings_dir ]; then
    echo "Could not find embeddings directory $embeddings_dir. Make sure to run embed_trajectories.sh first."
    exit 1
fi


# Loop over all the settings and run the training script
for env in $envs; do
    echo "Training $env with lr=$lr, l2_weight=$l2_weight, entropy_weight=$entropy_weight, n_layer=$n_layer"
    python basalt/train_bc.py \
        --embeddings_dir $embeddings_dir/$env \
        --output_dir $output_path/$env \
        --batch_size $batch_size \
        --n_epochs $n_epochs \
        --embedding_dim $embedding_dim \
        --downsampling $downsampling \
        --learning_rate $lr \
        --l2_weight $l2_weight \
        --entropy_weight $entropy_weight \
        --n_layers $n_layer \
        --save_every_epochs $save_every_n_epochs \
        --skip_noops \
        --skip_if_exists
done
