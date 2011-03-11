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
        // $("#layers #list").sortable(
        //     { 
        //         items: '.layer',
        //         containment: '#layers #list',
        //         cursor: 'move'
        //     }
        // );
        // $("#list").disableSelection();       
        // $("#modal").hide();    
    },

    setActivity: function(activity) {
        // this.activity = activity;
        // $("#layers .option a#add_layer").click(
        //     function(evt) {
        //         this.activity.addLayerClick(evt);
        // });        
    },

    showAddLayerDialog: function(isVisible) {
        // if (isVisible) {
        //     $("#modal").show();    
        // } else {
        //     $("#modal").hide();    
        // }
    }
});
 