var is_ie = !document.addEventListener;
var hl_focused = null;

function ready(){
    var anchor = window.location.hash;
    if(anchor){
        var hl_elem = document.getElementById(anchor.substring(1));
        hl_elem.classList.add('selected');
        if(hl_focused){
            hl_focused.classList.remove('selected');
        }
        hl_focused = hl_elem;
    }
    //TODO add older IE DOM selector
}

if(is_ie){
    document.attachEvent("onreadystatechange", function(){
        // check if the DOM is fully loaded
        if(document.readyState === "complete"){
            // remove the listener, to make sure it isn't fired in future
            document.detachEvent("onreadystatechange", arguments.callee);
            ready();
            window.onhashchange = ready;
        }
    });
}
else{
    if(document.readyState === "complete" || (document.readyState !== "loading" && !document.documentElement.doScroll)){
        ready();
        window.onhashchange = ready;
    }
    else{
        document.addEventListener("DOMContentLoaded", ready);
        window.onhashchange = ready;
    }
}
