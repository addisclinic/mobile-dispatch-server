// functions.js
// Released under BSD License
// Copyright Sana, 2014

var time_re = /^\d{2}:\d{2}:\d{2}?$/;
function bool(value){
    if(!value){ 
        return false;
    } else if (value == ""){
        return false;
    } else {
        return Boolean(value);
    }
}

function checkHourRange(val){
    var h = parseInt(val);
    return h >= 0 && h < 24; 
}

function checkMinSecRange(val){
    var ms = parseInt(val);
    return ms >= 0 && ms <= 59;
}

function isValidTime(value){
    var valid = false;
    try{
        if(value && value != ""){
            valid =  time_re.test(value);
        }
        // check ranges
        if(valid){
            var hms = String(value).split(":");
            var h = checkHourRange(hms[0])
            var m = checkMinSecRange(hms[1])
            var s = checkMinSecRange(hms[2]);
            valid = valid && h && m && s;
        }
    }
    catch(e) {
        alert(e);
        valid = false;
    }
    return valid;
}

// validates time and sets object background color to 
// light red, #ffaaaa if not valid
function validateJQueryObjTime(jqObj){
    var value = jqObj.val();
    var valid = isValidTime(value);
    if(!valid){
        jqObj.css("background-color","#ffaaaa");
        alert("Invalid Time!");
    } else {
        jqObj.css("background-color","#ffffff");
    }
    return valid;
}

function validateTime(obj)
{
    var timeValue = obj.value;
    if(timeValue == "" || timeValue.indexOf(":")<0)
    {
        alert("Invalid Time format");
        return false;
    }
    else
    {
        var sHours = timeValue.split(':')[0];
        var sMinutes = timeValue.split(':')[1];

        if(sHours == "" || isNaN(sHours) || parseInt(sHours)>23)
        {
            alert("Invalid Time format");
            return false;
        }
        else if(parseInt(sHours) == 0)
            sHours = "00";
        else if (sHours <10)
            sHours = "0"+sHours;

        if(sMinutes == "" || isNaN(sMinutes) || parseInt(sMinutes)>59)
        {
            alert("Invalid Time format");
            return false;
        }
        else if(parseInt(sMinutes) == 0)
            sMinutes = "00";
        else if (sMinutes <10)
            sMinutes = "0"+sMinutes;    

        obj.value = sHours + ":" + sMinutes;        
    }

    return true;    
}

function isValidDate(obj){
    
}
