var BASE_URL = 'https://go.pontifi.co/';
//var BASE_URL = 'http://localhost:8000/'

var CAPTCHA_ENDPOINT = 'captcha/';
var SUB_EMAIL_ENDPOINT = 'sub/';

function do_fetch(endpoint, success_callback, data){
    var is_post = data != undefined;

    var options = {
        method: is_post ? 'POST' : 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    }

    if(is_post){
        options['body'] = JSON.stringify(data);
    }

    fetch(BASE_URL + endpoint, options).then(function(response){
        // The API call was successful!
        if(response.ok){
            return response.json();
        }
        else{
            return Promise.reject(response);
        }
    }).then(function(data){
        // This is the JSON from our response
        success_callback(data);
    }).catch(function(err){
        // There was an error
        console.warn('Something went wrong.', err);
    });
}

var captcha_id = null;
var captcha_digest = null;

function handle_captcha(data){
    captcha_id = data['captcha_id'];
    captcha_digest = data['digest'];

    var captcha_container = document.getElementById('captcha-container');
    if(captcha_container.lastChild){
        captcha_container.removeChild(captcha_container.lastChild);
    }

    var img = document.createElement('img');
    img.src = 'data:image/png;base64, ' + data['img'];

    captcha_container.appendChild(img);
    document.getElementById('answer-input').value = '';
}

function update_captcha(){
    do_fetch(CAPTCHA_ENDPOINT, handle_captcha);
}

function show_msg(msg){
    var comment_error = document.getElementById('subscribe-error');
    comment_error.textContent = '';
    if(msg){
        comment_error.append(msg);
        comment_error.className = '';
    }
    else{
        comment_error.className = 'hidden';
    }
}

function refresh_form(){
    document.getElementById('subscribe-email').value = '';
    document.getElementById('answer-input').value = '';
    show_msg('');
    update_captcha();
}

function handle_post(data){

    console.log(data)

    if(!data['email_valid']){
        show_msg('Email address is invalid. Please try again.');
    }
    else if(!data['captcha_valid']){
        update_captcha();
        show_msg('Captcha error. Please try again.');
    }
    else if(data['email_exists']){
        //update_captcha();
        refresh_form();
        if(data['email_confirmed']){
            show_msg(data['email'] +'  is already subscribed.');
        }
        else{
            show_msg(data['email'] + ' is pending verificaton. Please click on the link in the confirmation Email to confirm.');
        }
    }
    else{
        refresh_form();
        show_msg(data['email'] + ' is now pending verification. Please verify by clicking on the link in the confirmation Email that will be sent shortly.')
    }
/*        update_captcha();
        show_msg('Captcha error. Please try again.');
    }

    refresh_form();*/
}

function submit_email(){
    var email = document.getElementById('subscribe-email').value.trim();
    if(email == ''){
        show_msg('Please enter a valid email.');
        return;
    }

    var answer = document.getElementById('answer-input').value.trim();
    if(answer == ''){
        show_msg('Please solve the captcha.');
        return;
    }

    var is_digest = document.getElementById('subscribe-digest').checked;

    var data = {'email': email, 'is_digest': is_digest, 'answer': answer, 'captcha_id': captcha_id, 'digest': captcha_digest}

    do_fetch(SUB_EMAIL_ENDPOINT, handle_post, data);

    return false;
}


////////////////////////////////////////////////////////////////

var is_ie = !document.addEventListener;

function ready(){
    var form = document.getElementById('subscribe-form');
    if(is_ie){
        form.attachEvent('onsubmit', function(evt){
            evt.preventDefault();
            //window.history.back();
            //post_comment();
            submit_email();
        });
    }
    else{
        form.addEventListener("submit", function(evt) {
            evt.preventDefault();
            //window.history.back();
            //post_comment();
            submit_email();
        }, true);
    }

    refresh_form();
}

if(is_ie){
    document.attachEvent("onreadystatechange", function(){
        // check if the DOM is fully loaded
        if(document.readyState === "complete"){
            // remove the listener, to make sure it isn't fired in future
            document.detachEvent("onreadystatechange", arguments.callee);
            ready();
        }
    });
}
else{
    if(document.readyState === "complete" || (document.readyState !== "loading" && !document.documentElement.doScroll)){
        ready();
    }
    else{
        document.addEventListener("DOMContentLoaded", ready);
    }
}
