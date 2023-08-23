#!/bin/bash
# Usage: bash download_demonstration_data.sh <basalt_data_dir> [max_data_size_in_mb_per_task]
# Example: bash download_demonstration_data.sh data_directory 1000
# This will create following folder structure:
# <basalt_data_dir>
#   VPT-models
#     foundation-model-1x.model
#     foundation-model-1x.weights
#   demonstrations
#     MineRLBasaltFindCave-v0
#      ...
#     MineRLBasaltMakeWaterfall-v0
#      ...
#     MineRLBasaltCreateVillageAnimalPen-v0
#      ...
#     MineRLBasaltBuildVillageHouse-v0
#      ...

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: bash download_demonstration_data.sh <basalt_data_dir> [max_data_size_in_mb_per_task]"
    echo "       max_data_size_in_mb_per_task is optional, specifying it will limit the size of each task's data."
    echo "       Example: bash download_demonstration_data.sh data_directory 1000"
    echo "       This will download total of 4 x 1000 MB of data, 1000 MB per task."
    exit 1
fi

# Create arguments for wget
if [ $# -eq 2 ]; then
    WGET_ARGS="--quota=${2}m"
else
    WGET_ARGS=""
fi

# Filelists are next to this script, so get the absolute path
FILELIST_DIR=$(dirname $(readlink -f $0))/filelists

DATA_DIR=$1
mkdir -p $DATA_DIR

# models
mkdir -p $DATA_DIR/VPT-models
wget -nc -i $FILELIST_DIR/openai-vpt-urls.txt -P $DATA_DIR/VPT-models
# Note: if you want to download 2x.model, you'll need to rename it to foundation-model-2x.model for consistency
#mv "$DATA_DIR/VPT-models/2x.model" "$DATA_DIR/VPT-models/foundation-model-2x.model"

# FindCave data
mkdir -p $DATA_DIR/demonstrations/MineRLBasaltFindCave-v0
wget -nc -i $FILELIST_DIR/FindCave_urls.txt -P $DATA_DIR/demonstrations/MineRLBasaltFindCave-v0 $WGET_ARGS

# MakeWaterfall data
mkdir -p $DATA_DIR/demonstrations/MineRLBasaltMakeWaterfall-v0
wget -nc -i $FILELIST_DIR/MakeWaterfall_urls.txt -P $DATA_DIR/demonstrations/MineRLBasaltMakeWaterfall-v0 $WGET_ARGS

# CreateVillageAnimalPen
mkdir -p $DATA_DIR/demonstrations/MineRLBasaltCreateVillageAnimalPen-v0
wget -nc -i $FILELIST_DIR/CreateVillageAnimalPen_urls.txt -P $DATA_DIR/demonstrations/MineRLBasaltCreateVillageAnimalPen-v0 $WGET_ARGS

# BuildVillageHouse
mkdir -p $DATA_DIR/demonstrations/MineRLBasaltBuildVillageHouse-v0
wget -nc -i $FILELIST_DIR/BuildVillageHouse_urls.txt -P $DATA_DIR/demonstrations/MineRLBasaltBuildVillageHouse-v0 $WGET_ARGS
