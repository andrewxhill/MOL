/**
 * The app object.
 */
var app = app || {};

app.openChannel = function() {    
    var channel = new goog.appengine.Channel(app.token),
        handler = {
            'onopen': app.onOpened,
            'onmessage': app.onMessage,
            'onerror': function(e) {console.log('ERROR ' + e.description);},
            'onclose': function() {console.log('closed');}
        },
        socket = channel.open(handler);
    socket.onopen = app.onOpened;
    socket.onmessage = app.onMessage;
};

app.updateMap = function() {
    console.log('Update map! points=' + app.state.points + ', limit=' + app.state.limit + ', offset=' + app.state.offset);
};

app.sendMessage = function(path, opt_param) {
    var xhr = new XMLHttpRequest();
    path += '?limit=' + app.state.limit;
    path += '&offset=' + app.state.offset;
    if (opt_param) {
        path += '&' + opt_param;
    }    
    xhr.open('POST', path, true);
    xhr.send();
};

app.onOpened = function() {
    app.sendMessage('/backend/points/opened');
};

app.onMessage = function(m) {
    var newState = JSON.parse(m.data);
    app.state.points = newState.points;
    app.state.limit = newState.limit;
    app.state.offset = newState.offset;
    app.updateMap();
};

      
/**
 * Gets extent from bounds. If bounds is null, null is returned. Otherwise
 * the geodesic in meters (the "extent") between the center of the bounds
 * and the southwest corner is returned.
 *
 * @param bounds google.maps.LatLngBounds
 */
app.getExtent = function(bounds) {
    if (bounds == null) {
        return 0;
    }
    var center = bounds.getCenter(),
    sw = bounds.getSouthWest(),
    extent = google.maps.geometry.spherical.computeDistanceBetween(center, sw);
    return extent;
};

/**
 * Gets the center of a Google geocode result given bounds. If bounds is null
 * the location is returned. Otherwise the bounds center is returned.
 */
app.getCenter = function(bounds, location) {
    if (bounds == null) {
        return location;
    }
    return bounds.getCenter();
};
 
/**
 * Displays Google geocoder web service results as markers on the map. Also
 * uses the geocalc web service to asynchronously calculate uncertainties
 * which are rendered as circles on the map around their corresponding marker.
 */
app.displayResults = function(results) {
    if (results.length == 0) {
        return;
    }
    var bounds = null,
        center = null,
        extent = null,
        marker = null,
        infowin = null,
        r = null,
        viewport = results[0].geometry.viewport,
        url,
        cb;
    app.callbacks = {};
    for (x in results) {
        r = results[x];
        bounds = r.geometry.bounds;
        center = app.getCenter(bounds, r.geometry.location);
        marker = new google.maps.Marker(
            {
                position: center,
                title: r.formatted_address,
                map: app.map
            }
        );
        extent = app.getExtent(bounds);
        url = app.getGeoCalcUrl(center, extent);
        app.geocoderMarkers.push(marker);
        cb = app.radiusCallback(marker, r, extent, url);
        app.callbacks[x] = cb;
        app.displayRadius(bounds, center, x, cb);            
        viewport.union(r.geometry.viewport);
    }
    app.map.fitBounds(viewport);
};
 
app.callbacks = {};

app.radiusCallback = function(marker, r, extent, url, x) {
    return function(radius) {
        url = url.replace('&callback=app.handleData', '');
        //marker.setMap(app.map);
        google.maps.event.addListener(
            marker, 
            'click', 
            app.markerClickHandler(marker, r, extent, url, x, radius));            
    };
};
 
app.markerClickHandler = function(marker, r, extent, url, x, radius) {
    return function() {
        var content = '<div id="content">' +
            '<h3>' + r.formatted_address + '</h3>' +
            'Point: ' + marker.getPosition().lat() + ', ' + marker.getPosition().lng() +
            '<br>Radius: ' + radius + 
            '<br><a target="_blank" href="' + url + '">Uncertainty calculation URL</a>' +
            '<br><a href="javascript::" class="zoom">zoom here</a>' +
            '</div>';
        var e = document.createElement('div');
        e.innerHTML = content;
        e.getElementsByClassName('zoom')[0].addEventListener(
            'click', function() {
                app.map.setZoom(12);
                app.map.panTo(marker.getPosition());
            }, false);        
        var infowin = new google.maps.InfoWindow({
            content: e
        });
        infowin.setPosition(marker.getPosition());
        infowin.open(app.map, marker);
    };
};
 
/**
 * AJAX call to geocalc service. Renders a circle on success. Adds circle
 * to app.geocoderMarkers.
 *
 */
app.displayRadius = function(bounds, center, x, cb) {
    var extent = app.getExtent(bounds);
    var url = app.getGeoCalcUrl(center, extent);
    var script = document.createElement("script");
    script.src = url + '&rid=' + x;
    document.body.appendChild(script);
};

app.handleData = function(data) {
    var point = new google.maps.LatLng(data.point.latitude, data.point.longitude),
        circle = new google.maps.Circle(
            {
                map : app.map,
                center : point,
                radius : data.radius,
                fillColor: '#CEE3F6',
                strokeWeight: 1
            }
        ),
        cb = app.callbacks[data.rid];
    app.geocoderMarkers.push(circle);
    cb(data.radius);
};


 
/**
 * Gets the geocalc web service URL for the given center point and bounding
 * box extent from a Google geocode result.
 */
app.getGeoCalcUrl = function(center, extent) {
    var url = app.GEO_CALC_URL;
    url = url.replace('EXTENT', String(extent));
    url = url.replace('LAT', String(center.lat()));
    url = url.replace('LNG', String(center.lng()));
    return url;
};
 
/**
 * Handler for the georeference button. Geocodes the address using Google
 * geocoder web service. On success it displays results as markers and
 * uncertainties as circles on the map. Adds a history token for the query.
 */
app.handleOnClick = function(evt) {
    var location = $('#location').val();
    if (location == '') {
        location = $('#location').attr('placeholder');
    }    
    // Adds a history token and eventually georeferences:
    //app.go(location);
    app.sendMessage('/backend/points/search', 'class=' + location);
};
 
/**
 * Cache for georeference results. Key is the location, results are the Google
 * geocoder results.
 */
app.cache = {};
 
/**
 * Success handler for the Google geocoder. 
 */
app.onSuccess = function(results) {
    app.clearOverlays();
    app.displayResults(results);
};
 
/**
 * Georeferences a location if not in the cache.
 */
app.georeference = function(location) {
    if (app.cache[location] != null) {
        app.onSuccess(app.cache[location]);
        return;
    }
    app.geocoder.geocode({'address': location}, function(results, status) {     
        if (status == google.maps.GeocoderStatus.OK) {
            app.cache[location] = results;
            app.clearOverlays();
            app.displayResults(results);
        } else {
            alert(status);
            app.handleClearMap();
            $('$button').focus();
        }        
    }); 
};
 
/**
 * Clears overlays from the map and resets json_results and location.
 */
app.handleClearMap = function(evt) {
    app.clearOverlays();
    $('#location').val('');
};
 
/**
 * Clears overlays from the map.
 */
app.clearOverlays = function() {
    if (app.geocoderMarkers) {
        for (i in app.geocoderMarkers) {
            app.geocoderMarkers[i].setMap(null);
        }
        app.geocoderMarkers.length = 0;
    }
};
 
/**
 * Goes to the page with results for q which is a location query and pushes a 
 * new history token.
 */
app.go = function(q) {
    app.setupPage(q);
    history.pushState(q, document.title, '?q=' + q);
};
 
/**
 * Handler for browser history events.
 */
onpopstate = function(event) {
    app.setupPage(event.state);
};
 
 
/**
 * Sets up the page based on the query history token. 
 */
app.setupPage = function(query) {
    if (query == null) {
        // Handles intitial page load with or without q param:
        var q = app.urlParams['q'];
        if (q == null) {
            app.handleClearMap();
            return;
        }
        $('#location').val(q);
        app.georeference(q);
    } else {
        $('#location').val(query);
        app.georeference(query);
    }
};
 
app.urlParams = {};

/**
 * Immediate function setup.
 */
app.init = function () {
    var e,
        a = /\+/g,  // Regex for replacing addition symbol with a space
        r = /([^&=]+)=?([^&]*)/g,
        d = function (s) { return decodeURIComponent(s.replace(a, " ")); },
        q = window.location.search.substring(1);

    // Open Channel API to App Engine
    app.openChannel();

    // Parses URL parameters:
    while ((e = r.exec(q))) {
        app.urlParams[d(e[1])] = d(e[2]);
    }
    
    var queryPlaceholder = "aves",
    latlng = new google.maps.LatLng(37.8, -121);
    app.mapOptions = {
        mapTypeId: google.maps.MapTypeId.TERRAIN,
        center: latlng
    };
    app.geocoder = new google.maps.Geocoder();
    app.map = new google.maps.Map(document.getElementById("map_canvas"), app.mapOptions);
    app.map.setZoom(3);
    app.geocoderMarkers = [];
    $('#button').click(app.handleOnClick);
    $('#clearMapButton').click(app.handleClearMap);
    $('#location').attr('placeholder', queryPlaceholder);
    $('#location').keyup(
        function(evt) {
            // Programatically clicks if keyup is the enter key:
            if (evt.keyCode === 13) {
                $('#button').click();
            }
        }, false);
};
