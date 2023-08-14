# Requires matplotlib and seaborn, i.e. you will need to run
# pip install matplotlib seaborn
# First run may take a while, after that it should be quick
import io
from typing import Dict, List, Tuple, Union

import matplotlib.pyplot as plt
import models
import pandas as pd
import seaborn as sns

sns.set_style("whitegrid")
sns.set_context("talk")
plt.rcParams["font.family"] = "Palatino"

# Choose green, yellow, red, and grey from Seaborn's deep palette
_, _, green, red, _, _, _, grey, yellow, _ = sns.color_palette("deep").as_hex()
ANSWER_COLOR_PALETTE = {
    "Yes": green,
    "No": red,
    "Win": green,
    "Draw": yellow,
    "Loss": red,
    "N/A": grey,
}

MAX_DATA_POINTS_FOR_ONE_ANSWER = 25


def plot_single_swarm(data, agent_name, **kwargs):
    # See make_dataframe_from_counts({'Yes': 10, 'No': 5}) for an example of
    # what data looks like
    plt.figure(figsize=(10, 5))
    print("num_votes_in_band: {}".format(data.shape[0]))
    ax = sns.swarmplot(
        data=data,
        x="Value",
        y="Answer",
        size=18,
        palette=ANSWER_COLOR_PALETTE,
        edgecolor="k",  # None, #'white',
        linewidth=1,
        **kwargs
    )
    ax.set_title(agent_name)

    # Remove irrelevant labels and ticks
    plt.xlabel("")
    plt.ylabel("")
    plt.grid(False)
    ax.get_xaxis().set_ticks_position("none")
    labels = [item.get_text() for item in ax.get_xticklabels()]
    empty_string_labels = [""] * len(labels)
    ax.set_xticklabels(empty_string_labels)

    ax.set_xlim([0, MAX_DATA_POINTS_FOR_ONE_ANSWER + 1])
    plt.subplots_adjust(top=0.95, bottom=0.05, right=0.98, left=0.1)
    # plt.margins(0,0)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", pad_inches=0.5, bbox_inches="tight")
    buffer.seek(0)

    return buffer


def make_dataframe_from_counts(counts):
    # See __main__ for an example of what counts looks like

    # Struggles with too many data points; normalize if that's the case
    max_num_datapoints = max(counts.values())
    if max_num_datapoints > MAX_DATA_POINTS_FOR_ONE_ANSWER:
        print("Too many data points, normalizing down")
        for key in counts:
            counts[key] = int(
                round(counts[key] * MAX_DATA_POINTS_FOR_ONE_ANSWER / max_num_datapoints)
            )
            # Just in case it rounds back up
            counts[key] = min(counts[key], MAX_DATA_POINTS_FOR_ONE_ANSWER)
        max_num_datapoints = max(counts.values())

    # This basically ensures that the bin with the most answers will look
    # roughly like a square (rather than e.g. being a very tall, narrow column)
    # If using this, make sure to increase figure height and decrease width
    # MAX_VALUE = max(2, int(round(sqrt(max_num_datapoints))))

    # Or, disable the square and have it be a single row
    MAX_VALUE = MAX_DATA_POINTS_FOR_ONE_ANSWER + 1

    answers_list = []
    values_list = []
    for answer, value in counts.items():
        answers_list.extend([answer] * value)
        values_list.extend([(i % MAX_VALUE) + 0.5 for i in range(value)])

    data = pd.DataFrame.from_dict({"Answer": answers_list, "Value": values_list})
    return data


def get_results_from_query(
    query: List[Tuple[models.Match, models.MatchResult, str]]
) -> Dict[str, Union[Dict[str, int], List[str]]]:
    """
    Calculates Win, Loss and Draw counts from query
    """
    results = [(tup[1].is_draw, tup[1].ranks, tup[2]) for tup in list(query)]
    _draw_count, _win_count, _lose_count = 0, 0, 0
    for result in results:
        is_draw = result[0]
        rank = result[1]
        episode = result[2]
        if is_draw:
            _draw_count += 1
        else:
            if episode == rank[0]:
                _win_count += 1
            else:
                _lose_count += 1

    return {
        "counts": {
            "Win": _win_count,
            "Draw": _draw_count,
            "Loss": _lose_count,
            "N/A": 0,
        },
        "order": ["Win", "Draw", "Loss", "N/A"],
    }


if __name__ == "__main__":
    # order=['Yes', 'No']
    # data = make_dataframe_from_counts({'Yes': 30, 'No': 10})
    order = ["Win", "Draw", "Loss", "N/A"]
    data = make_dataframe_from_counts({"Win": 8, "Draw": 2, "Loss": 1, "N/A": 5})
    plot_single_swarm(data, order=order)
