var show_details_last_id = -1;

function get_jobs() {
    var jobs = null;
    $.ajax({
        async : false,
        url : hostname.concat("/api/v1/jobs"),
        method : 'GET',
        dataType:'json',
        headers : {
            "Content-Type": "application/json",
            "Authorization": "Bearer ".concat(getToken())
        },
        success : function(data) {
            jobs = data.results;
        },
        error : function(data) {
            $('.alert-message').html('Couldn\'t fetch active jobs.');
            $('.alert').show();
        }
    });
    return jobs;
}

function get_job(id) {
    var job = null;
    $.ajax({
        async : false,
        url : hostname.concat("/api/v1/jobs/".concat(id)),
        method : 'GET',
        dataType:'json',
        headers : {
            "Content-Type": "application/json",
            "Authorization": "Bearer ".concat(getToken())
        },
        success : function(data) {
            job = data.job;
        },
        error : function(data) {
            $('.alert-message').html('Couldn\'t fetch the job selected.');
            $('.alert').show();
        }
    });
    return job;
}
  
function list_jobs() {
    $('.job-list-generated').remove();
    var jobs = get_jobs();
    var job_card_crud = $('#job-card-crud').clone();
    jobs.forEach(function (job, index) {
        var new_job = $('#job-card-crud').clone();
        $(new_job).addClass('job-list-generated');
        $(new_job).prop('id', 'job_card_crud-'.concat(String(index)));
        $(new_job).show();
        //$(new_job).find('.name').html(`#${job.id}: ${job.name}`);
        $(new_job).find('.name').html(job.name);
        $(new_job).find('.id').html(job.id);
        $(new_job).find('.created-on').html(moment(job.created_on).fromNow());
        if(job.progress_percentage < 100 && job.progress_percentage >= 0) {
            $(new_job).find('.processing').show();
        }
        else if (job.progress_percentage < 0) {
            $(new_job).find('.failed').show();
        }
        else {
            $(new_job).find('.completed').show();
            $(new_job).find('.results_url').prop('href', job.results_url);
            $(new_job).find('.results_url').show();
        }
        $(new_job).find('.images_url').prop('href', job.images_url);
        $('#jobs-list').append(new_job);
    });

    $(".show_details").click(function() {
        var id = $(this).find('.id').text();
        show_details(id);
    });
}

function show_details(id=-1) {
    if (id < 0) {
      if (!show_details_last_id || show_details_last_id < 0) {
        return true;
      }
      id = show_details_last_id;
    }
    show_details_last_id = id;
    $('#create_job').hide();
    $('#show_details').show();
    var current_job = get_job(id);
    if(!current_job) {
        window.location.href = '/dashboard';
        return;
    }
    $('#show_details .details').html('');
    $.each(current_job, function(index, value) {
        if(index == "status") {
            return;
        }
        $('#show_details .details').append(`<tr><td>${index}</td><td>${value}</td></tr>`);
    });

    $('.job-status-generated').remove();
    var status = JSON.parse(current_job.status);
    $.each(status, function(index, s) { 
        var new_status = $('#job-status-crud').clone();
        $(new_status).addClass('job-status-generated');
        $(new_status).prop('id', 'job_status_crud-'.concat(String(index)));
        $(new_status).show();
        $(new_status).find('.name').html(s.name);
        $(new_status).find('.start_time').html(moment(s.start_time).fromNow());
        $(new_status).find('.end_time').html(moment(s.end_time).fromNow());
        if(s.status) {
            $(new_status).find('.running').hide();
            $(new_status).find('.'.concat(s.status.toLowerCase())).show();
            $(new_status).addClass(s.status.toLowerCase());
        }
        $('#status-list').append(new_status);
    });
}

function create_job() {
    $('#show_details').hide();
    $('#create_job').show();
    show_details_last_id = -1;
}


function create_job_submit() {
    $('#create_job .btn-primary').prop('disabled', true);
    $('#create_job .btn-primary').addClass('disabled');
    var jobs = null;
    $.ajax({
        async : false,
        url : hostname.concat("/api/v1/jobs"),
        method : 'POST',
        dataType:'json',
        headers : {
            "Content-Type": "application/json",
            "Authorization": "Bearer ".concat(getToken())
        },
        data : JSON.stringify({
            "images_url" : $('#create_job input[id=images_file]').val(),
            "name" : $('#create_job input[id=name]').val(),
            "email" : $('#create_job input[id=email]').val()
        }),
        success : function(data) {
            $('#create_job').hide();
            $('.btn-primary').hide();
            list_jobs();
        },
        error : function(data) {
            $('.alert-message').html('Couldn\'t add new job.');
            $('.alert').show();
        }
    });
    return jobs;
}

function getSignedRequest(file){
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/sign_s3?file_name="+file.name+"&file_type="+file.type);
  xhr.setRequestHeader('Authorization', 'Bearer ' + getToken());
  xhr.onreadystatechange = function(){
    if(xhr.readyState === 4){
      if(xhr.status === 200){
        var response = JSON.parse(xhr.responseText);
        uploadFile(file, response.data, response.download_url);
      }
      else{
        $('.alert-message').html('Could not get signed URL.');
        $('.alert').show();
      }
    }
  };
  xhr.send();
}

function uploadFile(file, s3Data, url) {
  $('#create_job .btn-primary').addClass('disabled');
  $('#create_job .uploading-message').show();
  var xhr = new XMLHttpRequest();
  xhr.open("POST", s3Data.url);

  var postData = new FormData();
  for(key in s3Data.fields){
    postData.append(key, s3Data.fields[key]);
  }
  postData.append('file', file);

  xhr.onreadystatechange = function() {
    if(xhr.readyState === 4) {
      if(xhr.status === 200 || xhr.status === 204) {
        $('.file-upload').remove();
        $('.file-render #images_file').val(url);
        $('.file-render').show();
        $('#create_job .btn-primary').removeClass('disabled');
      }
      else{
        $('.alert-message').html('Could not upload file.');
        $('.alert').show();
      }
    }
  };
  xhr.send(postData);
}


function setupUploadFileInForm() {
  console.log("setup");
  $("#images_file_upload").change(function() {
    console.log("triggered");
    var files = document.getElementById("images_file_upload").files;
    var file = files[0];
    if(!file){
      return alert("No file selected.");
    }
    getSignedRequest(file);
  });
}
 
$(document).ready(function() {
    if(!isLoggedIn()) {
        window.location.href = '/';
    }

    list_jobs();
    setupUploadFileInForm();
    setInterval(list_jobs, 15000);
    setInterval(show_details, 15000);
});
