
/*
 * Safely prints to the console 
 */
/*
(function ($) {
  "use strict";
  $.fn.stdout = function(){
    var message,source,lineNo;
    
  };
}
*/
function stdout(message){
    if(window.console){
        console.log(message);
    }
}

function stdout(message,source){
    if(window.console){
        if(source){
            console.log(source + " : " + message);
        } else {
            console.log(message); 
        }
    }
}

function stdout(message, source, lineNo){
    if(window.console){
        if(source){
            if(lineNo){
                console.log(source + " --> " + lineNo + " : "+ message);
            } else {
                console.log(source + " : " + message);
            }
        } else {
                console.log(message); 
        }
    }
}