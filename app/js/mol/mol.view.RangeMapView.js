/**
 * Range map view for displaying range maps.
 * 
 * @constructor
 */
mol.view.RangeMapView = Backbone.View.extend(
{
    el: $('#map_canvas'),
    
    /**
     * Initialization.
     */
    initialize: function() {        
        var center = new google.maps.LatLng(0,0);            
        this.mapOptions = {
            zoom: 2,
            maxZoom: 20,
            center: center,
            mapTypeId: google.maps.MapTypeId.TERRAIN
        };
        this.metaControlDiv = document.createElement('div');
        var e = document.getElementById("map_canvas");
        this.map = new google.maps.Map(e, this.mapOptions);
        this.overlays = [];
    },

    renderPoints: function(json) {        
        var results = json,
            center = null,
            marker = null,
            infowin = null,
            lat = 0,
            lng = 0,
            radius = 0, 
            resources = [],
            occurrences = [],
            coordinate = null;
        for (provider in results.records.providers) {
            resources = results.records.providers[provider].resources;
            for (resource in resources) {
                occurrences = resources[resource].occurrences;
                for (coordinate in occurrences) {
                    coordinate = occurrences[coordinate].coordinates;
                    lat = parseFloat(coordinate.decimalLatitude);
                    lng = parseFloat(coordinate.decimalLongitude);
                    center = new google.maps.LatLng(lat, lng);
                    var donut = new google.maps.Circle({
                        map:this.map,
                        center: center,
                        radius: 50000,
                        strokeColor: "#414141",
                        strokeOpacity: 0.55,
                        strokeWeight: 1,
                        fillColor: "#0078ec",
                        fillOpacity: 0.5,
                        zIndex: 3
                      });   
                    this.overlays.push(donut);  
                    if (coordinate.coordinateUncertaintyInMeters != null) {
                        var cuim = parseFloat(coordinate.coordinateUncertaintyInMeters);
                        var opacity = 0.85;
                        if (cuim > 10000) { opacity = 0.4 };
                        var marker = new google.maps.Circle({
                            map:this.map,
                            center: center,
                            radius: cuim,
                            strokeColor: "#414141",
                            strokeWeight: 1,
                            strokeOpacity: opacity,
                            fillColor: "#ff5858",
                            fillOpacity: opacity,
                            zIndex: 5
                          });
                        //marker = new google.maps.Marker({position: center, map: this.map});
                        this.overlays.push(marker);   
                    }                                                      
                }
            }
        }
    },

    initMetadata: function(metadata) {
        this.metadata = metadata;        
        this.maxZoom = this.metadata.zoom;
        this.map.mapTypes[this.map.getMapTypeId()].maxZoom = parseInt(this.maxZoom);
        this.zoomToLayerExtent();
        this.attachMetadataControl(this.metaControlDiv, this.map);
        this.map.overlayMapTypes.insertAt(0, this.rangeImageMapType());
    },

    zoomToLayerExtent: function() {
      var data = this.metadata,
          nw = data.extentNorthWest.split(','),
          se = data.extentSouthEast.split(','),
          northW = new google.maps.LatLng(parseFloat(nw[0]),parseFloat(nw[1])),
          southE = new google.maps.LatLng(parseFloat(se[0]),parseFloat(se[1])),
          bounds = new google.maps.LatLngBounds;
        bounds.extend(northW);
        bounds.extend(southE);
        this.map.fitBounds(bounds);
    },
    
    attachMetadataControl: function(div, map) {    
        var metaBtn = document.createElement('div'),
            metaText = document.createElement('div'),
            self = this;
        metaBtn.style.backgroundColor = 'white';
        metaBtn.style.borderStyle = 'solid';
        metaBtn.style.borderWidth = '1px';
        metaBtn.style.cursor = 'pointer';
        metaBtn.style.textAlign = 'center';
        metaBtn.title = 'Click for range map metadata';
        div.style.padding = '8px';    
        div.appendChild(metaBtn);
        metaText.style.fontFamily = 'Lucida Grande, Trebuchet MS';
        metaText.style.fontSize = '12px';
        metaText.style.paddingLeft = '4px';
        metaText.style.paddingRight = '4px';
        metaText.innerHTML = '<b>Metadata</b>';
        metaBtn.appendChild(metaText);
        // TODO: Dispatch event to view:
        google.maps.event.addDomListener(
            metaBtn, 'click', function() {
                alert(JSON.stringify(self.metadata));
            });
        map.controls[google.maps.ControlPosition.TOP_RIGHT].push(div);
        div.index = 1;
    },


    /**
     * Returns normalized coordinates for a given map zoom level.
     * 
     * @param coord The coordinate
     * @param zoom The current zoom level
     */
    getNormalizedCoord: function(coord, zoom) {
        var y = coord.y,
            x = coord.x,
            tileRange = 1 << zoom;
        // don't repeat across y-axis (vertically)
        if (y < 0 || y >= tileRange) {
            return null;
        }
        // repeat across x-axis
        if (x < 0 || x >= tileRange) {
            x = (x % tileRange + tileRange) % tileRange;
        }
        return {
            x: x,
            y: y
        };
    },
    
    /**
     * The Google Maps ImageMapType for range map tiles.
     */
    rangeImageMapType: function() {   
        var self = this;
        return new google.maps.ImageMapType(
            {
                getTileUrl: function(coord, zoom) {
                    var normalizedCoord = self.getNormalizedCoord(coord, zoom),
                        speciesKey = self.metadata.mol_species_id;
                    if (!normalizedCoord) {
                        return null;
                    }
                    var bound = Math.pow(2, zoom);            
                    return "/layers/" + speciesKey + ".png?" +
                        "z=" + zoom + 
                        "&x=" + normalizedCoord.x + 
                        "&y=" + (normalizedCoord.y);
                },
                tileSize: new google.maps.Size(256, 256),
                isPng: true,
                opacity: 0.5
            });
    }
});
