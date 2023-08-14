$(document).ready(function() {
    if(isLoggedIn()) {
        window.location.href = '/dashboard';
    }
    $("#login-form").on("submit", function(){
        login();
    });
});
