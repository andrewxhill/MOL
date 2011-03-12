var layer = layer || {};

layer.init = function() {
    /* UI SETUP */
    $("#add_new_layer_dialog").css({'visibility':'visible'});
    $("#add_new_layer_dialog").children().hide();
    $("#add_new_layer_dialog").hide();
    
    $("#layers .option a#add_layer").click(
        function() {
            if ($("#add_new_layer_dialog").is(":visible")){
                $("#add_new_layer_dialog .dialog_button.output").hide();
                $("#add_new_layer_dialog").hide();
            }else{
                $("#add_new_layer_dialog").show();
                $("#add_new_layer_dialog .dialog_buttons").show();
                $("#add_new_layer_dialog").css({"height":"auto"});
            }
        });
        /*add click function to the add points button*/
        $('#add_points_button').click(function(){
            $("#add_new_layer_dialog .dialog_buttons").hide();
            $("#add_points_dialog input").attr({'value': "Artibeus concolor"});
            $("#add_points_dialog").show();
        });
        /*add click function to the add points button*/
        $('#add_range_button').click(function(){
            $("#add_new_layer_dialog .dialog_buttons").hide();
            $("#add_range_dialog input").attr({'value': "Artibeus concolor"});
            $("#add_range_dialog").show();
        });
            
        
    /* SETUP SORTABLE LAYER STACK */

    $("#layers #list").sortable(
        { 
            items: '.layer',
            containment: '#layers #list',
            cursor: 'move'
        });
    $("#list").disableSelection();
};
