function get_scores(divId, skip, limit) {
    $.ajax({
        url: `/scores.json?skip=${skip}&limit=${limit}`,
        type: 'GET',
        headers: {
            'Authorization': window.basalt_api_key,
        },
        success: function (agents){
            let tableBody = $("#"+divId+" tbody");
            for(let i=0; i<agents.length; i++){
                let agent = agents[i];
                let episodes = ``;
                for(let j=0; j<agent.episodes.length; j++){
                    let video_uri = agent.episodes[j].video_uri;
                    console.log(agent.episodes[j])
                    let video_hash = agent.episodes[j].hash.substring(0, 5)
                    episodes = episodes.concat(`
                        <a href="${video_uri}" target="_blank">
                            <code>
                                ${video_hash}
                            </code>
                        </a>
                    `)
                }
                tableBody.append(`
                    <tr>
                    <th scope="row">${i+1}</th>
                    <td><a href="/agents/win-lose.png?agent_name=${agent.name}"> ${agent.name} </a></td>
                    <td>${agent.task}</td>
                    <td>${agent.reputation_mu.toFixed(3)}</td>
                    <td>${agent.reputation_sigma.toFixed(3)}</td>
                    <td>${agent.score.toFixed(3)}</td>        
                    <td>
                        ${episodes}
                    </td>
                    </tr>
                `)
            }
        },
        error: function () {
            $("#"+divId).html(`
                <h2>Please login to use Human Evaluation Interface </h2>
            `)
        }
    })
}
