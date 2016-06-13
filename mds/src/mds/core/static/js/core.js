
var root="";
var ua = navigator.userAgent.toLowerCase();

function setRoot(newRoot){
  root = newRoot;
}

function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

function printMDSErrors(data){
    if(window.console){
        if(data){
            var errors = data['errors'];
            if(errors){
                for(var i=0;i < errors.length;i++) {
                    console.log(errors[i]);
                }
            } else {
                console.log("No errors returned");
            }
        } else {
            console.log("WARNING! Empty response from mds");
        }
    }
}

function handleMDSResponse(url,data, success,fail){
    try{
        var code = 500;
        if(data && data['code']){
            code = Number(data['code']);
        }
        if(code != 200){
            printMDSErrors(data);
            if(fail)
                fail(data);
        } else {
            if(success)
                success(data);
            else
                alert("Success! " + url);
        }
    } catch(err){
        if(window.console){ console.log("OOPS: " + url + ", " + err);}
        alert("Something went horribly wrong");
    }
}


function postAjax(url, data, success, fail){
    failHandler = function(data){
        if(window.console){ console.log("postAjax() Something went wrong posting");}
        if(fail)
            fail(data);
        else
            alert("Fail posting: " + url);
    };

    successHandler = function(data){
        if(window.console){ console.log("postAjax() Got an HTTP response" + url);}
        handleMDSResponse(url,data,success, failHandler);
    };
    $.ajax({
            url: url,
            type: 'post',
            data: data,
            headers: {
                "sessionid": readCookie("sessionid"),
                "csrftoken": readCookie("csrftoken")
            },
            dataType: 'json',
            success: successHandler,
            error: failHandler,
        });
    }

function postAjaxWithHeaders(url, data, headers, success, fail){
    failHandler = function(data){
        if(window.console){ console.log("postAjax() Something went wrong posting");}
        if(fail)
            fail(data);
        else
            alert("Fail posting: " + url);
    };

    successHandler = function(data){
        if(window.console){ console.log("postAjax() Got an HTTP response" + url);}
        handleMDSResponse(url,data,success, failHandler);
    };
    $.ajax({
            url: url,
            type: 'post',
            data: data,
            headers: headers,
            dataType: 'json',
            success: successHandler,
            error: failHandler,
    });
}

function getAjaxWithHeaders(url, data, headers, success, fail){
    failHandler = function(data){
        if(window.console){ console.log("getAjaxWithHeaders() Something went wrong fetching");}
        if(fail)
            fail(data);
        else
            alert("Fail executing GET: " + url);
    };

    successHandler = function(data){
        if(window.console){ console.log("getAjaxWithHeaders() Got an HTTP response" + url);}
        handleMDSResponse(url,data,success, failHandler);
    };
    $.ajax({
            url: url,
            data: data,
            headers: headers,
            dataType: 'json',
            success: successHandler,
            error: failHandler,
    });
}

function getPageWithHeaders(url, data, headers, success, fail){
    failHandler = function(data){
        if(window.console){ console.log("getAjaxWithHeaders() Something went wrong fetching");}
        if(fail)
            fail(data);
        else
            alert("Fail executing GET: " + url);
    };

    successHandler = function(data){
        if(window.console){ console.log("getAjaxWithHeaders() Got an HTTP response" + url);}
        document.load(data);
    };
    $.ajax({
            url: url,
            data: data,
            headers: headers,
            dataType: 'html',
            success: successHandler,
            error: failHandler,
    });
}

  function submitSubject(){
        var system_id = $('#id_system_id').val();
        var given_name = $('#id_given_name').val();
        var family_name = $('#id_family_name').val();
        var use_age  = $('#id_use_age').val();
        var age  = $('#id__age').val();
        var dob  = $('#id_dob').val();
        var gender = $('#id_gender').val();
        var image = $('#id_image').val();
        var location = $('#id_location').val();
        //var image = $('#id_image').files[0];

        if(window.console){
            console.log("system_id "+system_id);
            console.log("location " + location);
            console.log("image " + image);
        }
        var subject_uuid = "";
        $.post(root + '/mds/core/surgicalsubject/',{ 
                    system_id: system_id,
                    given_name: given_name,
                    family_name: family_name,
                    dob: dob,
                    gender: gender,
                    location: location,
                    image: image
                },function(data){ 
                    if(window.console){
                        console.log("SUCCESS ");
                    }
                    var msg = data['message'];
                    $('#task_patient_id').text(msg['system_id']).show();
                    $('#id_patient_uuid').val(msg['uuid']);
                    subject_uuid = msg['uuid'];
                    alert("Success Creating Patient:\n " + msg['system_id']);
                    //submitEncounter(subject_uuid);
                    //submitEncounterTasks(subject_uuid);
               }).fail(function(){
                    if(window.console){ console.log("Fail creating patient: ");}
                    alert("Failure creating patient! ");
                });
        return subject_uuid;
    }

function submitSubjectSSI(system_id, given_name, family_name, dob, gender, location, image,successCB,failCB){
        $.post(root + '/mds/core/surgicalsubject/',{ 
                    system_id: system_id,
                    given_name: given_name,
                    family_name: family_name,
                    dob: dob,
                    gender: gender,
                    location: location,
                    image: image
                },function(data){ 
                    if(window.console) { console.log("SUCCESS"); }
                    if(successCB){
                        successCB(data);
                    }
               }).fail(function(){
                    if(window.console){
                        console.log("FAIL");
                    }
                    if(failCB){
                       failCB();
                    }
                    //if(window.console){ console.log("Fail creating patient: ");}
                    //alert("Failure creating patient! ");
            });
    }

  function submitEncounter(){
        if(window.console){ console.log("submitEncounter()");}
        var subject = $('#id_patient_uuid').val();
        var observer = $('#id_observer_uuid').val();
        var concept = $('#id_encounter_concept_uuid').val();
        var procedure = $('#id_encounter_procedure_uuid').val();
        var device = $('#id_encounter_device_uuid').val();
        if(window.console){ console.log("posting: ( " + subject+", "
                + observer+", "+procedure+", "+concept+", "+ device +" )"); }
        var encounterCreated = false;
        var encounter_uuid = '';
        $.post(root + '/mds/core/encounter/',{ 
                    subject: subject,
                    procedure: procedure,
                    observer: observer,
                    device: device,
                    concept: concept
                },function(data){ 
                    var msg = data['message'];
                    if(window.console){ console.log("SUCCESS creating encounter" + msg['uuid']); }
                    
                    encounterCreated = true;
                    encounter_uuid = msg['uuid'];
                    alert("Success Entering Initial Encounter Data:\n " + msg['uuid']);
                    $('#id_encounter_uuid').val(msg['uuid']);
                    postObservations(encounter_uuid);
               }).fail(function(){
                    if(window.console){ console.log("Fail creating intake Encounter. ");}
                    alert("Failure creating encounter.");
                });
    }

    function postObservations(encounter_uuid){   
        //var encounter_uuid = $('#id_encounter_uuid').val();
        // Initial diagnosis
        var value = $('#id_diagnosis').val();
        if (value == "Other"){    
            value = $('#id_diagnosis_other').val();
        }
        postObs(encounter_uuid, '1', '104889a3-b6fa-4cdc-b232-d3b73e924cd1', value);
        // Operation(s)
        var value = $('#id_operation').val();
        var operations_other = $('#id_operations_other').val() || [];
        if(operations_other != null){
             value.push(operations_other);
        }
        postObs(encounter_uuid, '2', '9b01ef00-9fac-4f3c-87e5-66b152a3159b', value.join(","));
        // Operation date
        value= $('#id_date_of_operation').val();
        postObs(encounter_uuid, '3', '9082b5f8-74c6-4f54-a92b-04fa98e780d6', value);
        
        // Dicharge date
        value = $('#id_date_of_discharge').val();
        postObs(encounter_uuid, '4', '069ba5bb-a183-4d14-b485-9f93bca812c3', value);
        
        // Follow up date
        value = $('#id_date_of_regular_follow_up').val();
        postObs(encounter_uuid, '5', 'd24cf683-4b51-46d8-a4c4-154c38e1dd38', value);
    }

function postObs(encounter,node,concept,value,success,fail){
    if(success == null){
        success = function(data){
            if(window.console){ console.log("Succeeding  quietly...");}
        };
    }
    if(fail == null){
        fail = function(data){
            if(window.console){ console.log("Failing quietly...");}
        };
    }
    var url = root + '/mds/core/observation/';
    var data = { 
        encounter: encounter,
        node: node,
        concept: concept,
        value_text: value
    };
    var headers = {
                "sessionid": readCookie("sessionid"),
                "csrftoken": readCookie("csrftoken")
    };
    postAjaxWithHeaders(url,data,headers,success,fail);
}
 
function postTask(assigned_to,status, due_on, subject, procedure, concept){
    if(window.console){ console.log("posting task: ( " + assigned_to+", "+due_on
                                                    +", "+subject+", "+ procedure+" )"); }
    $.post(root + '/mds/tasks/encounter/',{ 
                    assigned_to: assigned_to,
                    status: status,
                    procedure: procedure,
                    subject: subject,
                    due_on: due_on,
                    concept: concept
    },function(data){ 
        var msg = data['message'];
        $('#id_encounter_uuid').val(msg['uuid']);
        alert("Success creating task: +\nDue on " + msg['due_on']);
    }).fail(function(){
        if(window.console){ console.log("Fail creating task: ");}
        alert("Failure creating task: +\nDue on " + msg['due_on']);
        //alert("Fail posting task: " + $('this'));
    });
}

/* 
*  Ajax version wich supports cookies
*/
function postTask2(assigned_to,status, due_on, subject, procedure,concept, success, fail){
    if(success == null){
        success = function(data){
            if(window.console){ console.log("Succeeding  quietly...");}
        };
    }
    if(fail == null){
        fail = function(data){
            if(window.console){ console.log("Failing quietly...");}
        };
    }
    var url = '/mds/tasks/encounter/';
    var data = {
        assigned_to: assigned_to,
        status: status,
        procedure: procedure,
        subject: subject,
        due_on: due_on,
        concept: concept
    };
    var headers = {
                "sessionid": readCookie("sessionid"),
                "csrftoken": readCookie("csrftoken")
    };
    postAjaxWithHeaders(url,data,headers,success,fail);
}

function postEncounterTask(assigned_to,status, due_on, subject, procedure,concept, headers, success, fail){
    if(success == null){
        success = function(data){
            if(window.console){ console.log("Succeeding  quietly...");}
        };
    }
    if(fail == null){
        fail = function(data){
            if(window.console){ console.log("Failing quietly...");}
        };
    }
    var url = '/mds/tasks/encounter/';
    var data = {
        assigned_to: assigned_to,
        status: status,
        procedure: procedure,
        subject: subject,
        due_on: due_on,
        concept: concept
    };
    if(headers == null){
        headers = {
                "sessionid": readCookie("sessionid"),
                "csrftoken": readCookie("csrftoken")
        };
    }
    postAjaxWithHeaders(url,data,headers,success,fail);
}


function submitEncounterTasks(){
        var subject = $('#id_patient_uuid').val()
        var status = 1;
        var assigned_to = $('#id_assigned_to_sa').val();
        var system_id = $('#id_system_id').val();
        
        // Initial procedure - both
        var procedure = $('#id_procedure').val();

        // initial follow up
        var due_on = $('#id_date_of_first_sa_follow_up').val() + " 23:59:59";
        var concept = "53dd9e7e-b025-489e-a507-921f540bd66b";
        postTask(assigned_to,status, due_on, subject, procedure, concept);

        // second regular follow up
        due_on = $('#id_date_of_second_sa_follow_up').val() + " 23:59:59";
        concept = "b6209098-d24d-4f39-ae82-577e2a4e6386";
        postTask(assigned_to,status, due_on, subject, procedure,concept);

        // 30 day follow up
        due_on = $('#id_date_of_final_sa_follow_up').val() + " 23:59:59";
        concept = "d908fe76-c210-4b9c-95f3-08eea37da1cb";
        postTask(assigned_to,status, due_on, subject, procedure,concept);
  }
