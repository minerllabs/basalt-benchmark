function match_update(hash, ranks, is_draw, eval_metadata = "{}", callback){
    var data = {
        hash: hash,
        ranks: ranks,
        is_draw: is_draw,
        eval_metadata: eval_metadata
    };

    console.log(data);

    if(document.location.pathname=="/demo-evaluation"){
        alert("This is a demo evaluation and the results will NOT be recorded. Please refresh page to try out an alternate match.");
        return;
    }

    $.ajax("/match/", {
        data : JSON.stringify(data),
        contentType : 'application/json',
        type : 'POST',
        headers : {
            'Authorization': basalt_api_key,
        },
        success: callback,
        error: function(jqXHR, exception){
            // Match result submitted too early
            if(jqXHR.status === 403 || jqXHR.status === 429){
                alert(jqXHR.responseJSON["detail"]);
            }else {
                // Reload page to get the new match
                location.reload();
                
                ///////////////////////////////////////////////////////////////////////////
                ///////////////////////////////////////////////////////////////////////////
                //
                // Make call to MTurk here !
                //
                ///////////////////////////////////////////////////////////////////////////
                ///////////////////////////////////////////////////////////////////////////
            }
        }
    });
}

function reset_match(match_data, task, are_eval_questions_required){
    // Initialize variables, setup html code for evaluation questions
    var match_hash = match_data.hash;

    $("#description").html(get_description(task));
    let questions = setup_evaluation(task, are_eval_questions_required);
    set_button_hover_event();

    // Construct a urlParams interface to obtain the GET params from URL 
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);


    window.EVALUATION_METADATA = {
        task_name: $("#moreInformationModalLabel code").html(),
        VIDEO_EVENTS: [],
        start_time: Date.now(),
        end_time: "NA",
        responses: {},
        win_player: "na",
        match_hash: false,
        ranks: false,
        is_draw: false,
        playerA_id: false,
        PlayerA_VIDEO_URL: false,
        playerB_id: false,
        PlayerB_VIDEO_URL: false,
        mturk_assignmentId: urlParams.get("assignmentId")?urlParams.get("assignmentId"):"N/A",
        mturk_hitId: urlParams.get("hitId")?urlParams.get("hitId"):"N/A",
        mturk_turkSubmitTo: urlParams.get("turkSubmitTo")?urlParams.get("turkSubmitTo"):"N/A",
        mturk_workerId: urlParams.get("workerId")?urlParams.get("workerId"):"N/A",                        
    }

    var video_event_logger = function(data){
        /** 
         * Event Handler for VideoPlayer events
         */
        // console.log(data);
        var currentPlayerId = $(data.target).attr("id").replace("_html5_api", "");
        var type = data.type;

        //console.log(currentPlayerId, type);
        

        window.EVALUATION_METADATA.VIDEO_EVENTS.push({
            type: type,
            source: currentPlayerId,
            time: Date.now(),
            player_id: $("#"+currentPlayerId+"_id").html()
        });
    }


    // Load videos
    // PlayerA
    var PlayerA_VIDEO_URL = match_data.episodes[0].video_uri;
    var PlayerA = videojs('playerA');
    PlayerA.src({type: 'video/mp4', src: PlayerA_VIDEO_URL});
    $("#playerA_id").html(
        match_data.episodes[0].hash
    )
    window.EVALUATION_METADATA.PlayerA_VIDEO_URL = PlayerA_VIDEO_URL

    PlayerA.eventTracking();
        
    PlayerA.on('tracking:firstplay', video_event_logger);
    PlayerA.on('tracking:first-quarter', video_event_logger);
    PlayerA.on('tracking:second-quarter', video_event_logger);
    PlayerA.on('tracking:third-quarter', video_event_logger);
    PlayerA.on('tracking:fourth-quarter', video_event_logger);    
    
    PlayerA.on('play', video_event_logger);


    // PlayerB
    var PlayerB_VIDEO_URL = match_data.episodes[1].video_uri;
    var PlayerB = videojs('playerB');
    PlayerB.src({type: 'video/mp4', src: PlayerB_VIDEO_URL});
    $("#playerB_id").html(
        match_data.episodes[1].hash
    )
    window.EVALUATION_METADATA.PlayerB_VIDEO_URL = PlayerB_VIDEO_URL

    PlayerB.eventTracking();
        
    PlayerB.on('tracking:firstplay', video_event_logger);
    PlayerB.on('tracking:first-quarter', video_event_logger);
    PlayerB.on('tracking:second-quarter', video_event_logger);
    PlayerB.on('tracking:third-quarter', video_event_logger);
    PlayerB.on('tracking:fourth-quarter', video_event_logger);    
    
    PlayerB.on('play', video_event_logger);    


    window.EVALUATION_METADATA.VIDEO_EVENTS = [];

    // Disable submit buttons for 30 seconds
    disable_submit();

    // Compile the evaluation answers and send a POST request to update match result
    window.scroll({top: 0,left: 0,behavior: 'smooth'});
    $("#id_evaluationForm").trigger("reset").one("submit", function (e) {
        e.preventDefault();

        // Mark evaluation end time
        window.EVALUATION_METADATA.end_time = Date.now();
        // Initialize variables
        let ranks = [match_data.episodes[0].hash, match_data.episodes[1].hash];
        let is_draw = false;

        // Get winner
        let win_player = $("input[name=winner]:checked").val();
        if(!win_player){
            return false;
        }
        if(win_player === "p1"){
            ranks = [match_data.episodes[0].hash, match_data.episodes[1].hash]
        } else if(win_player === "p2"){
            ranks = [match_data.episodes[1].hash, match_data.episodes[0].hash]
        } else if(win_player === "draw"){
            is_draw = true;
        }

        // Get evaluation answers
        let eval_answers = {
            "direct_question": [],
            "comparisons": [],
            "justificationText": $("#justificationText").val(),
            "notes": $("#id_notes").val()
        };
        for(let idx = 0; idx < questions["direct_question"].length; idx++){
            let question = questions["direct_question"][idx];
            // let answer_p1 = $("input[name=dq_q" + (idx+1) + "_p1]:checked").val();
            // let answer_p2 = $("input[name=dq_q" + (idx+1) + "_p2]:checked").val();

            let answer_p1 = $("#dq_q"+(idx+1)+"_p1").is(":checked");
            let answer_p2 = $("#dq_q"+(idx+1)+"_p2").is(":checked");

            eval_answers["direct_question"].push({
                "question": question,
                "player_1": (answer_p1 ? "true" : "false"),
                "player_2": (answer_p2 ? "true" : "false"),
            })
        }
        for(let idx = 0; idx < questions["comparison"].length; idx++){
            let question = questions["comparison"][idx];
            let answer = $("input[name=c_q" + (idx+1) + "]:checked").val();
            eval_answers["comparisons"].push({
                "question": question,
                "answer": (answer ? answer : ""),
            })
        }

        // store answers in metadata
        window.EVALUATION_METADATA.responses = eval_answers
        window.EVALUATION_METADATA.win_player = win_player
        window.EVALUATION_METADATA.match_hash = match_hash
        window.EVALUATION_METADATA.ranks = ranks
        window.EVALUATION_METADATA.is_draw = is_draw
        window.EVALUATION_METADATA.playerA_id = $("#playerA_id").html()
        window.EVALUATION_METADATA.playerB_id = $("#playerB_id").html()


        console.log(JSON.stringify(window.EVALUATION_METADATA));
        // Update match result

        var form_instance = $(this);
        match_update(
            match_hash, ranks, is_draw, JSON.stringify(window.EVALUATION_METADATA), function(new_match_data){

                // If its MTurk then do a form-submit                
                if(window.EVALUATION_METADATA.mturk_hitId != "N/A"){
                    // Set form action to the correct location
                    
                    var turk_submission_url = "#"
                    if(window.EVALUATION_METADATA.mturk_turkSubmitTo == "https://www.mturk.com"){
                        turk_submission_url = "https://www.mturk.com/mturk/externalSubmit";
                        
                    }else if(window.EVALUATION_METADATA.mturk_turkSubmitTo == "https://workersandbox.mturk.com"){
                        turk_submission_url = "https://workersandbox.mturk.com/mturk/externalSubmit";
                    }else{
                        alert("Unknown `turkSubmitTo` param provided: "+window.EVALUATION_METADATA.mturk_turkSubmitTo);
                        return;
                    }
                    console.log("Submitting to MTurk: " + turk_submission_url);
                    form_instance.attr("action", turk_submission_url);

                    $('#assignmentId').val(window.EVALUATION_METADATA.mturk_assignmentId);
                    $('#workerId').val(window.EVALUATION_METADATA.mturk_workerId);
                    $('#hitId').val(window.EVALUATION_METADATA.mturk_hitId);
                    //$('#evaluation_metadata').val(JSON.stringify(window.EVALUATION_METADATA));
                    
                    
                    if(window.EVALUATION_METADATA.mturk_assignmentId == "ASSIGNMENT_ID_NOT_AVAILABLE"){
                        // This is the case when the page is being viewed in Preview Mode. 
                        // Submission should not be allowed.
                        alert("You are attempting to submit the Form in Preview Mode. Please accept the Hit before submitting your response.");
                        return;
                    }else{
                        form_instance.submit();
                    }

                }else{
                    // Reset Match in case of local embed page render
                    reset_match(new_match_data, task, are_eval_questions_required);
                }
            }
        );
    })
}

function disable_submit() {
    $("#playerA_select,#playerB_select,#draw").prop('disabled', true);
    setTimeout(function () {
        $("#playerA_select,#playerB_select,#draw").prop('disabled', false);
    }, 30000);
}

function get_match(parentElementId, task, are_eval_questions_required) {
    $.ajax({
        url: "/match/?task="+task,
        type: "GET",
        headers: {
            'Authorization': basalt_api_key,
        },
        success: function(match_data){
            $("#loader").remove();
            $("#"+parentElementId).html("");
            $("#human_evaluation_interface").show();
            $("#evaluation_questions").show();
            reset_match(match_data, task, are_eval_questions_required);
        },
        error: function (jqXHR, exception){
            $("#loader").remove();
            $("#"+parentElementId).html("");
            $("#human_evaluation_interface").hide();
            $("#evaluation_questions").hide();
            if(jqXHR.status === 401){
                $("#"+parentElementId).html(`
                    <h2>Please login to use Human Evaluation Interface </h2>
                `).show();
            } else{
                alert(jqXHR.responseJSON["detail"]);
            }
        }
    });
}

function setup_interface(loginInfoId, are_eval_questions_required = false) {
    $("#human_evaluation_interface").hide();
    $("#evaluation_questions").hide();
    $("#id_tasks").change(function () {
        let task = $("#id_tasks").val();
        get_match(loginInfoId, task, are_eval_questions_required);
    })
}

function set_button_hover_event() {
    // Button class will change to `btn-primary` if mouse hover over a button and get back to `btn-secondary` on hover out
    $("#evaluation_questions label").each(function () {
        $(this).mouseenter(function () {
            if(!$("#"+$(this).attr('for')).is(':checked')){
                $(this).removeClass("btn-secondary");
                $(this).addClass("btn-primary");
            }
        }).mouseleave(function () {
            if(!$("#"+$(this).attr('for')).is(':checked')){
                $(this).removeClass("btn-primary");
                $(this).addClass("btn-secondary");
            }
        }).removeClass("btn-primary").addClass("btn-secondary");
    })
}

function set_button_click_event(radioName) {
    return; // disabling temporarily
    // Event to make checked radio button's class `btn-primary` and rest to `btn-secondary`
    $("input[name=" + radioName + "]").on("change", function (){
        $("input[name=" + radioName + "]").each(function () {
            $("label[for='" + $(this).attr('id') + "']").removeClass('btn-primary').addClass('btn-secondary');
        });
        $("label[for='" + $("input[name=" + radioName + "]:checked").attr('id') + "']").removeClass('btn-secondary').addClass('btn-primary');
    })
}

function setup_evaluation(task, is_required) {
    // Add html code on reset match for evaluation questions
    

    // Get questions for the task
    let ques = get_questions(task);

    let is_required_text_marker = (is_required ? `<code>*</code>` : ``);
    let is_required_attr_marker = (is_required ? `required` : ``);

    set_button_click_event("winner");

    // Add html code for `Direct questions`
    let direct_question = $("#directQuestion");
    direct_question.html("").append(`
        <div class="row">
            <div class="col-md-12 text-center mt-4">
                <h3 style="font-size:1.25rem">Direct questions</h3>
            </div>
        </div>
    `)
    for(let idx=1; idx <= ques["direct_question"].length; idx++){
        let question = ques["direct_question"][idx-1];
        direct_question.append(`
        <tr>
            <td id="text_dq_q${idx}">
                <b>Q${idx}.</b> ${question} ${is_required_text_marker}
            </td>
            <td class="text-center">
                <div class="form-check form-control-lg" style="text-align: center">
                    <input class="form-check-input" type="checkbox" value="" name="dq_q${idx}" id="dq_q${idx}_p1"/>
                </div>
            </td>
            <td class="text-center">
                <div class="form-check form-control-lg" style="text-align: center">
                <input class="form-check-input" type="checkbox" value="" name="dq_q${idx}" id="dq_q${idx}_p2"/>
                </div>
            </td>
        </tr>
        `)

        set_button_click_event("dq_q"+idx);
        set_button_click_event("dq_q"+idx);
    }

    // Add html code for `Comparison` questions
    let comparisons = $("#comparisons");
    comparisons.html("").append(`
        <h3 class="mt-4 mb-4"> Question Set <code>#2</code> </h3>
    `)
    for(let idx=1; idx <= ques["comparison"].length; idx++){
        let question = ques["comparison"][idx-1];
        comparisons.append(`
        <div class="row mb-2">
            <div class="col-md-8" id="text_c_q${idx}">
            <b>Q${idx}.</b> ${question} ${is_required_text_marker}
            </div>
            <div class="col-md-4">

                <div class="btn-group" role="group" aria-label="">
                    <!-- Left -->
                    <input type="radio" class="btn-check" name="c_q${idx}" id="c_q${idx}_p1" value="p1" autocomplete="off" ${is_required_attr_marker}>
                    <label class="btn btn-outline-primary" for="c_q${idx}_p1">Left Player</label>

                    <!-- Draw -->
                    <input type="radio" class="btn-check" name="c_q${idx}" id="c_q${idx}_draw" value="draw" autocomplete="off" ${is_required_attr_marker}>
                    <label class="btn btn-outline-primary" for="c_q${idx}_draw">Draw</label>

                    <!-- Right -->
                    <input type="radio" class="btn-check" name="c_q${idx}" id="c_q${idx}_p2" value="p2" autocomplete="off" ${is_required_attr_marker}>
                    <label class="btn btn-outline-primary" for="c_q${idx}_p2">Right Player</label>

                    <!-- N/A -->
                    <input type="radio" class="btn-check" name="c_q${idx}" id="c_q${idx}_na" value="na" autocomplete="off" ${is_required_attr_marker} checked="checked">
                    <label class="btn btn-outline-primary" for="c_q${idx}_na">N/A</label>
                </div>

            </div>
        </div>
        `)

        set_button_click_event("c_q"+idx);
    }
    return ques;
}


function get_human_readable_task_name(task_name){
    switch(task_name){
        case "FindCave":
            return "Find Cave";
            break;
        case "MakeWaterfall": 
            return "Make Waterfall";
            break;
        case "BuildVillageHouse":
            return "Build Village House";
            break;
        case "CreateVillageAnimalPen":
            return "Create Village Animal Pen";
            break;
        default:
            return "Unkown Task Name";
    }
}

