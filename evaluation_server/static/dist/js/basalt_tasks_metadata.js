function get_questions(task){
    let questions={};
    questions["direct_question"] = [];
    questions["comparison"] = [];
    if(task === "FindCave"){
        questions["direct_question"] = [
            "Did this player find and enter a cave?"
        ]
        questions["comparison"] = [
            "Which player found a cave the fastest? (If neither found a cave, that is a draw.)",
            "Which player moved more quickly and efficiently?",
            "Which player was better at looking for caves in areas they hadn't already explored?",
            "Which player was better at going to areas where it is more likely to find caves?",
            "Which player was better at noticing potential caves that entered its field of vision?",
            "Which player was better at realizing when it has successfully found a cave? (In other words, which player was better at properly ending the minigame once it had entered a cave?)",
            "Which player seemed more human-like (rather than a bot or computer player)?"
        ]
    } else if(task === "MakeWaterfall"){
        questions["direct_question"] = [
            "Did this player create a waterfall?",
            "Did this player end the video while looking at a player-constructed waterfall?"
        ]
        questions["comparison"] = [
            "Which player moved more efficiently?",
            'Which player chose a better location for their waterfall? (If neither player created a waterfall, select "Draw".)',
            'Which player took a better "picture" of the waterfall? (If neither player took a picture of a player-constructed waterfall, select "Draw".)',
            "Which player seemed more human-like (rather than a bot or computer player)?"
        ]
    } else if(task === "CreateVillageAnimalPen"){
        questions["direct_question"] = [
            "Did the player harm the village? Examples include taking animals from existing pens, damaging existing houses or farms, and attacking villagers.",
            "Did the player build an enclosed space (pen) from which animals could not escape? (For this question, it is okay if the pen did not contain animals).",
            "Did the player's pen contain at least two animals of the same type?",
            "Did the player's pen contain only one type of animal (if pen contained no animals, answer is no. Monsters and villagers are not counted)?",
            "Did the player's pen have at least one gate that would allow players to enter and exit (using a block to jump over fence does not count)?",
            "Was the player's pen built next to a house?"
        ]
        questions["comparison"] = [
            "Which player chose a better location for their pen in the village?",
            "Which player searched more effectively for animals to pen?",
            "After finding the animals, which player penned them more effectively?",
            "Which player seemed more human-like (rather than a bot or computer player)?"
        ]
    } else if(task === "BuildVillageHouse"){
        questions["direct_question"] = [
            "Did the player harm the village? Examples include taking animals from existing pens, damaging existing houses or farms, and attacking villagers."
        ]
        questions["comparison"] = [
            "Which player chose a better location for their house?",
            "Which player's structure seemed most like a house?",
            "Which player was better at removing unnecessary blocks (or never placing unnecessary blocks)?",
            "Which player was better at using the appropriate type of blocks (i.e. the ones that are used in other houses in the village)?",
            "Which player's house better matched the \"style\" of the village?",
            "Which player built the better-looking house?",
            "Which player seemed more human-like (rather than a bot or computer player)?"
        ]
    }
    return questions
}

function get_description_items(task) {
    if(task === "FindCave"){
        return ["The player should search for a cave, and terminate the episode when it is inside one."]
    } else if(task === "MakeWaterfall"){
        return ["After spawning in a mountainous area, the player should build a beautiful waterfall and then reposition itself to take a scenic picture of the same waterfall.", "The picture of the waterfall is can be taken by facing the waterfall at a good angle and then terminating the episode."]
    } else if(task === "CreateVillageAnimalPen"){
        return ["After spawning in a (plains) village, the player should build an animal pen next to one of the houses in a village.", "Animal pens must contain two of a single kind of animal (you are only allowed to pen chickens, cows, pigs, sheep or rabbits).", "The animal pen should not contain more than one type of animal." ,"Don't harm the village. Players may terraform the area around a house to build a pen.", "When we say not to harm the village, examples include taking animals from existing pens, damaging existing houses or farms, and attacking villagers."]
    } else if(task === "BuildVillageHouse"){
        return ["The player should build a new house in the style of the village (random biome), in an appropriate location (e.g. next to the path through the village), without harming the village in the process.",
        "Then the player should give a brief tour of the house (i.e. spin around slowly such that all of the walls and the roof are visible)."]
    } else{
        return ""
    }
}

function get_description(task) {
    var description_items = get_description_items(task);

    var response = '<ul>';
    for(var i=0; i<description_items.length; i++){
        response += '<li>'+description_items[i]+'</li>';
    }
    response += '</ul>';
    return response;
}
