var layer = layer || {};

layer.init = function() {
    var default_new_layer_dialog = $('<button type="button">Add Range Map</button><button type="button">Add Points</button>');
    $("#add_new_layer_dialog").append(default_new_layer_dialog).hide();
    $("#layers #list").sortable(
        { 
            items: '.layer',
            containment: '#layers #list',
            cursor: 'move'
        });
    $("#list").disableSelection();
    
    $("#layers .option a#add_layer").click(
        function() {
            if ($("#add_new_layer_dialog").is(":visible")){
                $("#add_new_layer_dialog").css({"height":"0px"}).hide();
            }else{
                $("#add_new_layer_dialog").css({"height":"auto"}).show();
            }
        });
    
};
