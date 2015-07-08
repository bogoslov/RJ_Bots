/**
 * Purpose: Javascript functions for Bundle Viewer work
 * User: Aleksey Bogoslovskyi
 * Date: 10.06.13
 */


function ConfirmDelete(modal){
    document.getElementById(modal).submit();
}
function update_content(type, entity){
    $.ajax({
        type: "GET",
        url: "./content/",
        data: {"type": type, "entity": entity},
        success: function(data){
            $("#content").html(data);
        }
    });
    return false;
}

function disable_option(){
    var dropdown = document.getElementById('servers');
    dropdown.options[0].disabled=true;
}

function get_option(type, entity, div_id){
    var dropdown = document.getElementById('servers');
    $.ajax({
        type: "GET",
        url: "./content/",
        data: {"type": type, "entity": entity, "server": dropdown.options[dropdown.selectedIndex].text},
        success: function(data){
            $("#"+div_id).html(data);
        }
    });
    return false;
}


