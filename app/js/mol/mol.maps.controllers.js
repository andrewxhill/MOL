mol.maps.controllers.PointsController = function(config) {    
    if (!(this instanceof mol.maps.controllers.PointsController)) {
        return new mol.maps.controllers.PointsController(config);
    }
    this.init(config);
    return this;
};

mol.maps.controllers.PointsController.prototype = (
    function() {
        var map = null,
            data = null,
            overlays = [];
        
        var init = function(config) {
            map = mol.rangeMap.map;
            data = config.data;
            renderPoints();
        };
        
        
        var showAll = function() {
            toggle(true);
        };
        
        var hideAll = function() {
            toggle(false);
        };

        var toggle = function(visible) {
            for (x in overlays) {
                if (visible) {
                    overlays[x].setMap(map);
                } else {
                    overlays[x].setMap(null);
                }
            }
        };

        var renderPoints = function() {        
            var center = null,
                marker = null,
                infowin = null,
                lat = 0,
                lng = 0,
                radius = 0, 
                resources = [],
                occurrences = [],
                coordinate = null,
                iconUrl = 'http://labs.google.com/ridefinder/images/mm_20_red.png';
            for (provider in data.records.providers) {
                resources = data.records.providers[provider].resources;
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
                                map: map,
                                icon: iconUrl
                            }
                        );
                    
                        overlays.push(marker);                      
                        if (coordinate.coordinateUncertaintyInMeters != null) {
                            var cuim = parseFloat(coordinate.coordinateUncertaintyInMeters);
                            radius = cuim;
                            var opacity = 0.85;
                            if (cuim > 10000) { 
                                opacity = 0.4; 
                            }
                            var circle = new google.maps.Circle(
                                {
                                    map: map,
                                    center: center,
                                    radius: cuim,
                                    fillColor: '#CEE3F6',
                                    strokeWeight: 1,                                
                                    zIndex: 5
                                });
                            overlays.push(circle);
                        }                                                      
                        var providerName = data.records.providers[provider].name;
                        var resourceName = resources[resource].name;
                        var sourceUrl = data.sourceUrl;
                        google.maps.event.addListener(
                            marker, 
                            'click', 
                            markerClickHandler(marker, radius, providerName, resourceName, sourceUrl)
                        );                                
                    }
                }
            }
        };

        var markerClickHandler = function(marker, radius, provider, resource, url) {
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
                        map.setZoom(12);
                        map.panTo(marker.getPosition());
                    }, false);        
                var infowin = new google.maps.InfoWindow(
                    {
                        content: e
                    }
                );
                infowin.setPosition(marker.getPosition());
                infowin.open(map, marker);
            };
        };
        
        return {
            init: init,
            hideAll: hideAll,
            showAll: showAll            
        };
        
}());