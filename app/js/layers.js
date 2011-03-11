var layer = layer || {};

layer.init = function() {
    $("#layers #list").sortable(
        { 
            items: '.layer',
            containment: '#layers #list',
            cursor: 'move'
        });
    $("#list").disableSelection();
    
    $("#layers .option a#add_layer").click(
        function() {
            $('#modal').show();
        });
    $("#modal").hide();    
};
