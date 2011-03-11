var layer = layer || {};

layer.loading = function(source,type,value){
    var id = source+"_"+type+"_"+value;
    id = id.toUpperCase().split(' ').join('_');
    var layerstack = $("<div>").attr({"id":id,"class":"layer list"})
        .append($('<img src="/static/loading-small.gif" />').height("16px"))
        .append('<span class="layer source">' + source + '</span>' + value);
    $("#list").prepend(layerstack);
}
layer.remove = function(id){
    /* should add a safety check here */
    $(".layer.list").remove("#"+id);
}
layer.init = function() {
    /* Add Layer Setup*/
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
        
        /* start the add layer method from the search bar */
        $("#gbif_points_search").click(function(){
            $("#add_points_dialog").hide();
            $("#add_new_layer_dialog").hide();
            var val = $("#gbif_points_search_box").val();
            layer.loading("GBIF","points",val);
        });
        $("#mol_range_search").click(function(){
            $("#add_range_dialog").hide();
            $("#add_new_layer_dialog").hide();
            var val = $("#mol_range_search_box").val();
            layer.loading("MOL","range",val);
        });
        
    /* Delete Layer Setup */
    $("#layers .option a#delete_layer").click(function(){
        var id = $("#layers .layer.list input:checked").parent().attr('id');
        console.log(id);
        layer.remove(id);
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
