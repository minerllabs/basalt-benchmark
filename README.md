# MineRL BASALT Benchmark code and dataset

This code package contains links and instructions for downloading/using the demonstration and evaluation datasets presented in the paper "BEDD: The MineRL BASALT Evaluation and Demonstrations Dataset for Training and Benchmarking Agents that Solve Fuzzy Tasks".

This code repository contains an example implementation of behavioural cloning using the demonstration dataset.

## Demonstration dataset

`scripts/filelists/*.txt` contains text files which list links for downloading the individual trajectories for the demonstration dataset. You can use `wget` or your favorite download tools to download the files. We have also included `scripts/download_demonstration_data.sh` to download the data using `wget`, e.g. `./scripts/download_demonstration_data.sh path_to_directory_for_data`. Note that this requires ~700GB of space on disk to download fully.

## Evaluation dataset

Evaluation dataset is available in at the following Zenodo record: [https://zenodo.org/record/8021960](https://zenodo.org/record/8021960).

For using the dataset to do human evaluation, see `evaluation_server/README.md` for further instructions.

## Setup the environment for training the BC model

Tested system: Ubuntu with 16 CPU cores, 64GB of RAM and Nvidia Tesla T4 GPU.
Additional requirements: `sudo apt install xvfb ffmpeg`

```bash
conda env create -f environment.yml
conda activate basalt
# Install the `basalt` library so that it is available anywhere.
# This is also required for running the code.
pip install -e .
```

## Testing the training pipeline

For small-scale test-run (5GB of data downloaded, minimal amount of training), run `./scripts/test_pipeline.sh`.

This will do the following:
1) Download 5GB of data: a small subset of data for each BASALT task + smallest OpenAI VPT foundation model for playing Minecraft.
2) Embed the dataset using the VPT model (turn video frames into smaller embeddings).
3) Train a behavioural cloning agent on top of the embeddings using `imitation` library
4) Roll out the trained model in Minecraft to produce the videos ready for human evaluation.

This will create a new directory `pipeline_test_data`, which will contain all the downloaded data, trained models and resulting rollouts.

If everything is succesful, you should have a directory `pipeline_test_data/rollouts/` directory with following structure:

```
pipeline_test_data/rollouts/
├── MineRLBasaltBuildVillageHouse-v0
│   ├── seed_12658.jsonl
│   ├── seed_12658.mp4
|   ...
│   ├── seed_99066.jsonl
│   └── seed_99066.mp4
├── MineRLBasaltCreateVillageAnimalPen-v0
│   ├── seed_14975.jsonl
│   ├── seed_14975.mp4
|   ...
│   ├── seed_85236.jsonl
│   └── seed_85236.mp4
├── MineRLBasaltFindCave-v0
│   ├── seed_14169.jsonl
│   ├── seed_14169.mp4
|   ...
│   ├── seed_95099.jsonl
│   └── seed_95099.mp4
└── MineRLBasaltMakeWaterfall-v0
    ├── seed_12095.jsonl
    ├── seed_12095.mp4
    ...
    ├── seed_95674.jsonl
    └── seed_95674.mp4
```

These video files are now ready to be used for human evaluation. See `evaluation_server/README.md` for instructions how to setup the server and gather human rankings of this agent versus the ones shared in the Evaluation Dataset.


## Running full experiment

For full training, run following scripts. Make sure the experiment output directory `basalt_output_directory` has at least 1TB of free space, as this will place all downloaded and produced data there.

```bash
basalt_output_directory="/path/to/place/for/all/the/data"
bash ./scripts/download_demonstration_data.sh $basalt_output_directory
bash ./scripts/embed_trajectories.sh $basalt_output_directory
bash ./scripts/train_bc.sh $basalt_output_directory
bash ./scripts/rollout_bc.sh $basalt_output_directory
```

Whole process takes roughly 2-3 days on a 16-core, 64GB RAM, Nvidia Tesla T4 system.

## License

MIT. See `LICENSE`

Contents under `basalt/vpt_lib` are originally from [this repository](https://github.com/openai/Video-Pre-Training), shared under MIT license.