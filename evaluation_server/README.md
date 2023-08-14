# BASALT Human Evaluation Interface

This directory contains a server application with a database to register new agents, upload/add their rollout videos in Minecraft and then ask humans for their preferences on which of the agents performed tasks better.

# Steps to evaluate your BASALT solution against the baselines

*Requirements*: The .mp4 video files of your agent solving the MineRL BASALT tasks, following the benchmark instructions. You should have 11 videos per task (44 in total). See the root `README.md` for training and rolling out an example solution.


### Step 1) Create the Python environment

Ideally, create a new Python environment (tested with Python 3.9 using conda environment), and install the requirements with `pip install -r requirements.txt`.

### Step 2) Download the Evaluation Dataset with BASALT baselines

Download the BASALT baseline agent videos and 3000 human answers to kick-start your evaluation from this Zenodo record: [https://zenodo.org/record/8021960](https://zenodo.org/record/8021960).

### Step 3) Start the evaluation server

In one terminal, start the evaluation server in this directory: `uvicorn main:app --host 0.0.0.0` . This will start the evaluation server, and you should be able to see the page if you go to [http://localhost:8000/](http://localhost:8000/).

### Step 4) Initialize the database with BASALT baselines

In a separate terminal, use the following command to add the baseline solutions, their videos and the existing human evaluations to the database:

`python initialize_database_with_baseline_results.py --path_to_baseline_answers /path/to/human_answers.json --path_to_banned_workers_json /path/to/banned_workers.json  --all_rollouts_dir /path/to/agent_videos`

You can find the required data in the [evaluation dataset]([https://zenodo.org/record/8021960]). Path to the `agent_videos` should be path to a directory containing the different agents (e.g., `Random`, `Human1`).

### Step 5) Add your agent rollouts to the database

Use following command to add your agent to the database:

`python add_agent_for_evaluation.py --agent_name your_agent_name_here --rollout_dir /path/to/rollouts`

The `/path/to/rollouts` should be path to a directory that contains the rollouts in the same format as example behavioural cloning produces (see root `README.md` of this repository).

### Step 6) Collect human answers

Direct human evaluators to the following URL: [localhost:8000/embed](localhost:8000/embed)

You should be prompted with a random pairing of the agents (may not be your agent), and ask for answers. Once answering one question, the page will refresh and new pair of agents will be shown.

Providing answers will update the TrueSkill rating of agents behind the scene, and new pairs are generated, priortizing pairs which will reduce most uncertainty in answers.

### Step 7) Collect your agent results

You can find the leaderboard at: [http://localhost:8000/scores](http://localhost:8000/scores) . This shows the TrueSkill ratings for each agent, separate by task.

