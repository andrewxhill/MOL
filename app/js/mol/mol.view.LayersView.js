/**
 * Layers dialog view.
 * 
 * @constructor
 */
mol.view.LayersView = Backbone.View.extend(
{
    /**
     * Initialization.
     */
    initialize: function() {   
        var self = this;
        
        var pathArray = window.location.pathname.split( '/' );
        var speciesName = pathArray[4].charAt(0).toUpperCase() + pathArray[4].slice(1);
        speciesName = speciesName.split('_').join(' ');
        
        /* Add Layer Setup*/
        $("#add_new_layer_dialog").css({'visibility':'visible'});
        $("#add_new_layer_dialog").children().hide();
        $("#add_new_layer_dialog").hide();
        $("#layers .option a#add_layer").click(
            function() {
                if ($("#add_new_layer_dialog").is(":visible")){
                    $("#add_new_layer_dialog .dialog_button.output").hide();
                    $("#add_new_layer_dialog").hide();
                } else {
                $("#add_new_layer_dialog").show();
                    $("#add_new_layer_dialog .dialog_buttons").show();
                    $("#add_new_layer_dialog").css({"height":"auto"});
                }
        });
        /* add mouseover and mouseexit for hiding the overlay */
        $("#widget-container").mouseover(function(){
            self.menuFocus(true);
        });
        /* add mouseover and mouseexit for hiding the overlay */
        $("#widget-container").mouseleave(function(){
            self.menuFocus(false);
        });
        $("#widget-container .option.list").each(function(){
            if ($(this).attr('id') != 'add'){ $(this).hide('slow') };
        });
        
        
        /*add click function to the add points button*/
        $('#add_points_button').click(
            function(){
                $("#add_new_layer_dialog .dialog_buttons").hide();
                $("#add_points_dialog input").attr({'value': speciesName});
                $("#add_points_dialog").show();
            }
        );
        /*add click function to the add points button*/
        $('#add_range_button').click(
            function(){
                $("#add_new_layer_dialog .dialog_buttons").hide();
                $("#add_range_dialog input").attr({'value': speciesName});
                $("#add_range_dialog").show();
            }
        );
        
        /* start the add layer method from the search bar */
        $("#gbif_points_search").click(
            function(){
                $("#add_points_dialog").hide();
                $("#add_new_layer_dialog").hide();
                var val = $("#gbif_points_search_box").val();
                self.loading("GBIF", "points", val, self);
            }
        );
        $("#mol_range_search").click(
            function(){
                $("#add_range_dialog").hide();
                $("#add_new_layer_dialog").hide();
                var val = $("#mol_range_search_box").val();
                self.loading("MOL", "range", val, self);
            }
        );
        
        /* Delete Layer Setup */       
        $("#layers .option a#delete_layer").click(
            function(){
                var id = $("#layers .layer.list input:checked").parent().attr('id');
                console.log(id);
                self.remove(id);
            }
        );
    
        
        /* SETUP SORTABLE LAYER STACK */
        $("#layers #list").sortable(
            { 
                items: '.layer',
                containment: '#layers #list',
                cursor: 'move'
            }
        );
        $("#list").disableSelection();
    },
    
    menuFocus: function(focus) {
        var self = this;
        if (focus) {
            self.timeout = 1;
            /* show */
            $("#widget-container .option.list").show('slow');
            $("#widget-container #list").show('slow');
        } else {
            if (self.timeout == 1){
                self.timeout = 0;
                setTimeout(function(){
                    self.menuFocus(false);
                 }, 4500);
            } else {
                /* hide */
                $("#widget-container #list").hide('slow');
                $("#widget-container .option.list").each(function(){
                    if ($(this).attr('id') != 'add'){ $(this).hide('slow') };
                });
            }
        }
    },
    
    remove: function(speciesKey) {
        /* should add a safety check here */
        $(".layer.list").remove("#"+speciesKey);
    },

    doneLoading: function(id) {
        $("#"+id+" .loading").remove();
        $("#"+id).prepend('<input type="radio" name="layer-toggle" value="range" CHECKED>');
    },
    
    stackOrder: function(){
        var order = {},
            n = 0;
        $(".layer list").each(function(){
            order[n] = $(this).attr("id");
            n++;
        });
        return order;
    },
    
    addLayerControl: function(id, source, value){
        var layerstack = $("<div>").attr({"id":id,"class":"layer list"})
            .append($('<img src="/static/loading-small.gif" class="loading"/>').height("16px"))
            .append('<span class="source">' + source + '</span>' + value);
        $("#list").prepend(layerstack);
    }
    
    loading: function(source, type, value, self) {
        var id = source+"_"+type+"_"+value;
        id = id.toLowerCase().split(' ').join('_');
        self.addLayerContorl(id, source, value);
        self.activity.handleAddPoints(source, type, value, id);
    },
    
    setActivity: function(activity) {
        this.activity = activity;
    }
});
 
