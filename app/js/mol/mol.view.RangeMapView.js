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
        this.currentRangeIndex = 0;
        this.rangeMaps = {};
        var e = document.getElementById("map_canvas");
        this.map = new google.maps.Map(e, this.mapOptions);
        this.overlays = {};
        this.layersDiv = document.getElementById('content');
        this.attachLayersControl(this.layersDiv, this.map);
    },

    renderPoints: function(json, id) {        
        var results = json,
            center = null,
            marker = null,
            infowin = null,
            lat = 0,
            lng = 0,
            radius = 0, 
            resources = [],
            occurrences = [],
            coordinate = null,
            iconUrl = 'http://labs.google.com/ridefinder/images/mm_20_red.png';
        if (!this.overlays.hasOwnProperty(id)) {
            this.overlays[id] = [];            
        }
        for (provider in results.records.providers) {
            resources = results.records.providers[provider].resources;
            for (resource in resources) {
                occurrences = resources[resource].occurrences;
                for (coordinate in occurrences) {
                    coordinate = occurrences[coordinate].coordinates;
                    lat = parseFloat(coordinate.decimalLatitude);
                    lng = parseFloat(coordinate.decimalLongitude);
                    center = new google.maps.LatLng(lat, lng);
                    marker = new google.maps.Marker(
                        {
                            position: center,
                            map: this.map,
                            icon: iconUrl
                        }
                    );
                    // var donut = new google.maps.Circle({
                    //     map:this.map,
                    //     center: center,
                    //     radius: 50000,
                    //     strokeColor: "#414141",
                    //     strokeOpacity: 0.55,
                    //     strokeWeight: 1,
                    //     fillColor: "#0078ec",
                    //     fillOpacity: 0.5,
                    //     zIndex: 3
                    //   });   
                    
                    this.overlays[id].push(marker);                      
                    if (coordinate.coordinateUncertaintyInMeters != null) {
                        var cuim = parseFloat(coordinate.coordinateUncertaintyInMeters);
                        radius = cuim;
                        var opacity = 0.85;
                        if (cuim > 10000) { 
                            opacity = 0.4; 
                        }
                        var circle = new google.maps.Circle(
                            {
                                map: this.map,
                                center: center,
                                radius: cuim,
                                fillColor: '#CEE3F6',
                                strokeWeight: 1,                                
                                zIndex: 5
                          });
                        //marker = new google.maps.Marker({position: center, map: this.map});
                        this.overlays[id].push(circle);
                    }                                                      
                    var providerName = results.records.providers[provider].name;
                    var resourceName = resources[resource].name;
                    var sourceUrl = results.sourceUrl;
                    google.maps.event.addListener(
                        marker, 
                        'click', 
                        this.markerClickHandler(marker, radius, providerName, resourceName, sourceUrl)
                    );                                
                }
            }
        }
    },

    markerClickHandler: function(marker, radius, provider, resource, url) {
        var self = this;
        return function() {
            var content = '<div id="content">' +
                '<h3>' + provider + ': ' + resource + '</h3>' +
                'Point: ' + marker.getPosition().lat() + ', ' + marker.getPosition().lng() +
                '<br>Radius: ' + radius + 
                '<br><a target="_blank" href="' + url + '">Source URL</a>' +
                '<br><a href="javascript::" class="zoom">zoom here</a>' +
                '</div>';
            var e = document.createElement('div');
            e.innerHTML = content;
            e.getElementsByClassName('zoom')[0].addEventListener(
                'click', function() {
                    self.map.setZoom(12);
                    self.map.panTo(marker.getPosition());
                }, false);        
            var infowin = new google.maps.InfoWindow(
                {
                    content: e
                }
            );
            infowin.setPosition(marker.getPosition());
            infowin.open(self.map, marker);
        };
    },
    
    deleteMapLayer: function(id){
        for (var i in this.overlays[id]){
            this.overlays[id][i].setMap(null);
        }
        delete this.overlays[id];
    },

    showLayer: function(layerId, isVisible, layerType){
        var map = isVisible ? this.map : null,
            index = 0,
            speciesKey = 'animalia/species/' + layerId.split('species_')[1];
        if (layerType === 'points') {
            for (var i in this.overlays[layerId]){
                this.overlays[layerId][i].setMap(map);
            }
        } else {
            index = this.rangeMaps[layerId];
            if (isVisible) {
                this.map.overlayMapTypes.insertAt(index, this.rangeImageMapType(speciesKey));
            } else {
                this.map.overlayMapTypes.removeAt(index);
            }
        }
    },
    
    addRangeMap: function(metadata, id) {
        var speciesKey = metadata.mol_species_id;
        this.metadata = metadata;        
        this.maxZoom = this.metadata.zoom;
        this.map.mapTypes[this.map.getMapTypeId()].maxZoom = parseInt(this.maxZoom);
        this.zoomToLayerExtent();
        this.attachMetadataControl(this.metaControlDiv, this.map);        
        this.map.overlayMapTypes.insertAt(this.currentRangeIndex, this.rangeImageMapType(speciesKey));
        this.rangeMaps[id] = this.currentRangeIndex;
        this.currentRangeIndex = this.currentRangeIndex + 1;
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

    attachLayersControl: function(div, map) {    
        map.controls[google.maps.ControlPosition.RIGHT_TOP].push(div);
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
    rangeImageMapType: function(speciesKey) {   
        var self = this;
        return new google.maps.ImageMapType(
            {
                getTileUrl: function(coord, zoom) {
                    var normalizedCoord = self.getNormalizedCoord(coord, zoom);
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
