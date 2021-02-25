var BASE_URL = 'https://go.pontifi.co/';
//var BASE_URL = 'http://localhost:8000/'

var CAPTCHA_ENDPOINT = 'captcha/';
var COMMENT_ENDPOINT = 'comments'; // omit trailing slash

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

function show_error(msg){
    var comment_error = document.getElementById('comment-error');
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
    document.getElementById('comment-input').value = '';
    document.getElementById('answer-input').value = '';
    show_error('');
    update_captcha();
}

function get_comment_element(comment_item){
    var div = document.createElement('div');
    div.innerHTML = comment_item['comment_src'].trim();
    div.className = 'reader-comment';
    var timestamp = document.createElement('div');
    timestamp.innerText = comment_item['timestamp']
    timestamp.className = 'comment-timestamp';
    div.prepend(timestamp)
    return div;
}

function handle_init(data){
    var comment_list = document.getElementById('comment-list');

    for(var i=0; i < data.length; i++){
        var item = data[i];
        var comment_elem = get_comment_element(item);
        comment_list.appendChild(comment_elem);
    }
}

function handle_post(data){

    if(data['captcha_valid']){
        refresh_form();
        var comment_list = document.getElementById('comment-list');
        var new_comment = get_comment_element(data['comment_data']);
        comment_list.prepend(new_comment);
    }
    else{
        update_captcha();
        show_error('Captcha error. Please try again.');
    }
}

function post_comment(){
    var comment = document.getElementById('comment-input').value.trim();
    if(comment == ''){
        show_error('Please enter a comment.');
        return;
    }

    var answer = document.getElementById('answer-input').value.trim();
    if(answer == ''){
        show_error('Please solve the captcha.');
        return;
    }

    var data = {'comment': comment, 'answer': answer, 'captcha_id': captcha_id, 'digest': captcha_digest}

    do_fetch(COMMENT_ENDPOINT, handle_post, data);

    return false;
}


////////////////////////////////////////////////////////////////

var is_ie = !document.addEventListener;

function ready(){
    var form = document.getElementById('comment-form');
    if(is_ie){
        form.attachEvent('onsubmit', function(evt){
            evt.preventDefault();
            //window.history.back();
            //post_comment();
            post_comment();
        });
    }
    else{
        form.addEventListener("submit", function(evt) {
            evt.preventDefault();
            //window.history.back();
            //post_comment();
            post_comment();
        }, true);
    }

    // set COMMENT_ENDPOINT
    var pathname = window.location.pathname;
    COMMENT_ENDPOINT += pathname;

    // populate existing comments
    do_fetch(COMMENT_ENDPOINT, handle_init); //TESTING CBI

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
