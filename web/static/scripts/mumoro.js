OpenLayers.ImgPath = "/static/img/openlayers/";

function Mumoro(lonStart, latStart, lonDest, latDest,
                fromHash, hashUrl, layers, cloudmadeapi){
    this.lonStart = lonStart;
    this.latStart = latStart;
    this.lonDest = lonDest;
    this.latDest = latDest;
    this.fromHash = fromHash;
    this.hashUrl = hashUrl;
    
    var icon_standard = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
    icon_standard.graphicWidth = 26;
    icon_standard.graphicHeight = 41;
    icon_standard.graphicXOffset = -icon_standard.graphicWidth/2;
    icon_standard.graphicYOffset = -icon_standard.graphicHeight;
    icon_standard.graphicOpacity = 1.0;
    icon_standard.pointRadius = 6;
    this.icon['start'] = OpenLayers.Util.extend({}, icon_standard);
    this.icon['start'].externalGraphic = "/static/img/pin-d.png";
    this.icon['dest']  = OpenLayers.Util.extend({}, icon_standard);
    this.icon['dest'].externalGraphic = "/static/img/pin-a.png";      
    
    this.geojson_reader= new OpenLayers.Format.GeoJSON({'internalProjection': this.proj900913,
							'externalProjection': this.proj4326});
    var self = this;
    this.map = new OpenLayers.Map("map",
			     {
				 maxExtent: new OpenLayers.Bounds(-230256.98428, 6100548.77175, -121945.71522, 6147786.85522),
				 restrictedExtent: new OpenLayers.Bounds(-230256.98428, 6100548.77175, -121945.71522, 6147786.85522),
				 // maxResolution: 156543.0399,
				 // numZoomLevels: 19,
				 units: 'm',
				 projection: this.proj900913,
				 displayProjection: this.proj4326,
				 controls: [
				     new OpenLayers.Control.Navigation({zoomWheelEnabled: true}),
				     new OpenLayers.Control.ScaleLine(),
				     (this.isTouchDevice() ? 
				      new OpenLayers.Control.MobileDragPan(): 
				      new OpenLayers.Control.PanZoomBar())
				 ]
			     }
			    );
    // Define the map layer
    // Other defined layers are OpenLayers.Layer.OSM.Mapnik, OpenLayers.Layer.OSM.Maplint and OpenLayers.Layer.OSM.CycleMap
    var cloudmade = new OpenLayers.Layer.CloudMade("CloudMade", {
						       key: cloudmadeapi,
						       styleId: 31494,
						       opacity: 1,
						       minZoomLevel: 1,
						       maxZoomLevel: 5
						   });
    this.map.addLayer(cloudmade);
    var styleMap = new OpenLayers.StyleMap({strokeWidth: 2});
    styleMap.addUniqueValueRules("default", "layer", 
				 {"Foot": { strokeColor : "#4e9a06",
					    strokeDashstyle: "1 8",
					    strokeWidth: 5},
				  "Bus": { strokeColor : "${color}",
					    strokeWidth: 5,
					    strokeDashstyle: 'longdash'},
				  "Bike": {strokeColor : "#204a87"},
				  "marker": {graphicWidth: 49,
					     graphicHeight: 39,
					     graphicXOffset: -12,
					     graphicYOffset: -39,
					     graphicOpacity: 1.0,
					     externalGraphic: "/static/img/${marker_icon}",
					     cursor: 'pointer'
				  },
				  "connection": {strokeColor : "#4e9a06",
						 strokeDashstyle: "1 8",
						 strokeWidth: 5}});
    this.routeLayer = new OpenLayers.Layer.Vector("Route", {styleMap: styleMap});

    function onPopupClose(evt) {
	selectControl.unselect(this.feature);
    }

    function onBeforeFeatureSelect(evt){
	var feature = evt.feature;
	if(feature.attributes.type == "bus_departure" || feature.attributes.type == "bike_departure"){
	    return true;
	}else {
	    return false;
	}
    }
    function onFeatureSelect(evt) {
	var feature = evt.feature;
	if(feature.attributes.type == "bus_departure" || feature.attributes.type == "bike_departure"){
	    var popup = new OpenLayers.Popup.
		FramedCloud("featurePopup",
			    feature.geometry.getBounds().getCenterLonLat(),
                            new OpenLayers.Size(100,100),
			    feature.attributes.type == "bus_departure" ? self.bus_popup_content(feature) : self.bike_popup_content(feature),
                            null, false, onPopupClose);
	    popup.displayClass="translucent";
	    feature.popup = popup;
	    popup.feature = feature;
	    self.map.addPopup(popup);
	}
    }
    function onFeatureUnselect(evt) {
	var feature = evt.feature;
	if (feature.popup) {
            self.map.removePopup(feature.popup);
            feature.popup.destroy();
            feature.popup = null;
	}
    }
    this.routeLayer.events.on({'featureselected': onFeatureSelect,
    			       'featureunselected': onFeatureUnselect,
			       'beforefeatureselected': onBeforeFeatureSelect,
			       'featureadded': onFeatureSelect
    			      });
    this.map.addLayer(this.routeLayer);
    this.map.addLayer(this.layerMarkers);
    // Location support
    if (navigator.geolocation) {  
	navigator.geolocation.watchPosition(function(p){self.refreshPosition(p);});
    }
    
    // map.addLayer(bikeLayer);
    // bikeLayer.setZIndex(730);
    var controlDrag = new OpenLayers.Control.
    	DragFeature(this.layerMarkers, {
    			// 'onStart': function(feature) {
    			//     feature.style.graphicOpacity = 0.5;
    			// },
    			'onComplete': function(feature) {
    			    var lonlat = new OpenLayers.LonLat(feature.geometry.x,feature.geometry.y);
    			    var ll = self.MToLonLat(lonlat);
    			    feature.style.graphicOpacity = 1.0;
    			    self.nodes['fmouse_'+feature.data]=true;
    			    self.reverseGeocoding(lonlat,feature.data);
    			    self.setMark(lonlat,feature.data);
    			}
    		    });
    this.map.addControl(controlDrag);
    controlDrag.activate();

    var selectControl = new OpenLayers.Control.
	SelectFeature([this.routeLayer, this.layerMarkers], {clickout: true,
							     multiple: true});

    this.map.addControl(selectControl);
    selectControl.activate();

    $("#map").contextMenu({menu: 'myMenu'},
			  function(action, el, pos) {
			      var tmp = {'x': pos.x,
					 'y': pos.y};          
			      self.handleClick(tmp, action);
			  });
    // init ui
    
    $('#time-select').change(function(){
			  var v = $(this).val();
			  if(v == 'later'){
			      $('#later-time-select').show();
			  } else {
			      $('#later-time-select').hide();
			      self.time_set_in(v);
			  }
		      });
    $("#date-picker").datepicker();
    $("hour-picker").change(function(){
				self.time_set_hour($(this).val());
			    });
    $("minutes-picker").change(function(){
				self.time_set_minutes($(this).val());
			    });
    
    if( this.fromHash ) {
        var tmpStart = new OpenLayers.LonLat(this.lonStart, this.latStart);
        var tmpDest = new OpenLayers.LonLat(this.lonDest, this.latDest);
        this.nodes['start'] = {
	    'lon': lonStart,
	    'lat': latStart
        };
        this.nodes['dest'] = {
	    'lon': lonDest,
	    'lat': latDest
        };
        this.setMark(tmpStart,"start");
        this.setMark(tmpDest,"dest");
	this.centerToMap(tmpStart,tmpDest);
        this.compute();
    }
    else {
        var s = {'lon': lonStart,
		 'lat': latStart};
        var d = {'lon': lonDest,
		 'lat': latDest};
        this.centerToMap(s,d);
	self.time_set_in($('#time-select').val());
    }
}

Mumoro.prototype = {
    proj4326: new OpenLayers.Projection("EPSG:4326"), // longitude/latitude in decimal degrees
    proj900913: new OpenLayers.Projection("EPSG:900913"), // Google projection
    nodes: {
	'start': null,
	'dest': null,
	'fmouse_start': true,
	'fmouse_dest': true            
    },
    disableClickEvent: false,
    icon_standard: undefined,
    icon: {
	'start': null,
	'dest': null
    },
    bikeLayer: null,
    layerMarkers: new OpenLayers.Layer.Vector("Markers"),
    node_markers: {
	'start': null,
	'dest': null
    },
    paths: undefined,
    cacheStart: "",
    cacheDest: "",

    time_set_in: function(minutes){
	this.time_set_as(new Date(new Date().getTime() + minutes * 60000));
    },

    time_set_as: function(d){
	$('#time').val(pad(d.getDate()) + '/' + pad(d.getMonth()) + '/' + d.getFullYear() + ' ' + 
		       pad(d.getHours()) + ':' + pad(d.getMinutes()));
	if( this.areBothMarked() ) { 
            this.compute();
	}
    },

    isTouchDevice: function() {
	var el = document.createElement('div');
	el.setAttribute('ontouchstart', 'return;');
	if(typeof el.ontouchstart == "function"){
	    return true;
	}else {
	    return false;
	}
    },

    bus_popup_content: function(feature){
	return $('<div/>').append($('<div/>',{'class': 'bus-popup'}).append($('<h2/>').
				  append($('<img/>', 
					   {src: '/static/img/' + 
					    feature.attributes.line_icon})).
				  append("vers " + feature.attributes.headsign)

).
	    append($('<p/>').append("Monter à <span class='departure'>"+ 
				    feature.attributes.stop_area +
				    "</span> à " + 
				    this.secondesToHuman(feature.attributes.start_time))).
	    append($('<p/>').append("Descendre à <span class='arrival'>"+ 
				    feature.attributes.dest_stop_area + 
				    "</span> à " + 
				    this.secondesToHuman(feature.attributes.arrival_time)))).html();
    },

    bike_popup_content: function(feature){
	return $('<div/>').append($('<div/>',{'class': 'bike-popup'}).append($('<h2/>').
				  append("Le Vélo STAR")).
	    append($('<p/>').append("Prendre un vélo à la borne <span class='departure'>"+ 
				    feature.attributes.station_name + 
				    "</span>")).
	    append($('<p/>').append("Déposer le vélo à la borne <span class='arrival'>"+ 
				    feature.attributes.dest_station_name + 
				    "</span>"))).html();
    },

    cleanup_path: function(){
	var map = this.map;
	while(map.popups.length){
	    var p = map.popups[0];
	    map.removePopup(p);
	    p.destroy();
	}
	this.routeLayer.destroyFeatures();	
    },

    disp_path: function(id) {
	this.cleanup_path();
	var features = this.geojson_reader.read(this.paths[id]);
	if(features){
            this.routeLayer.addFeatures(features);
	    $('#path_costs tr').removeClass("selected");
	    $('#path_costs tr.path-' + id).addClass("selected");
	}
    },
    
    compute: function(){
	var self=this;
	if( this.areBothMarked() ){
            $.getJSON("path", {slon: this.nodes['start'].lon, 
			       slat: this.nodes['start'].lat,
			       dlon: this.nodes['dest'].lon,
			       dlat: this.nodes['dest'].lat,
			       time: $("#time").val()
			      },
		      function(data) {
			  $("#info").show();
			  if(data.error){
			      $("#info > h2").html("Itinéraires");
			      $('#path_costs').html($('<p/>', {'class': 'error'}).text(data.error));
			      self.cleanup_path();
			      $("#hash_url").html('');
			  }
			  else {
			      $("#info > h2").html("Mobi’Rennes propose " + data.paths.length + " itinéraire" + (data.paths.length > 1 ? "s" : ""));
			      $("#path_costs").html(self.itineraries_descriptions(data));
			      self.paths = data.paths;
			      self.disp_path(0);
			      if( !self.fromHash )
				  self.addToHash();
			  }
		      });
	}
    },
    
    itineraries_descriptions: function(data){
	var self = this;
	return $('<table/>').
	    append($('<tbody>').each(function(){
					 var tbody = $(this);
					 $.each(data.paths, function(i,p){
				  var time = p.cost[0];
				  tbody.append($('<tr/>',{'class': 'path-'+i}).append($('<td/>').each(
									    function(id,td){
$.each($.grep(p.features, 
	       function(f){ return f.properties.icon;}),
      function(id, f){ $(td).append($('<img/>',
			       { src: "/static/img/" + f.properties.icon }));});}

							    )).append($('<td/>').append(self.
							 transformToDurationString(time))).
					       click(function(){self.disp_path(i);})

);});}));

    },

    setDepFromGeo: function(){
	this.setDepOrDestFromGeo('start');
    },

    setDestFromGeo: function(){
	this.setDepOrDestFromGeo('dest');
    },

    setDepOrDestFromGeo: function(target){
	var self = this;
	var pos = this.current_position;
	self.setMark({'lon': pos.coords.longitude,
		      'lat': pos.coords.latitude
		     }, target);
    },

    handleClick: function(coord, mark) {
	var lonlat = this.map.getLonLatFromViewPortPx(coord);
	lonlat.transform(this.proj900913, this.proj4326);
	this.nodes['fmouse_'+mark]=true;
	this.setMark(lonlat, mark);
    },
    
    // Coordinates in 4326 projection (lon/lat)
    setMark: function(lonlat, mark){
	this.nodes[mark] = lonlat;
	if(this.node_markers[mark]) {
            this.layerMarkers.removeFeatures(this.node_markers[mark]);
            this.node_markers[mark].destroy();
            this.node_markers[mark] = null;
	}
	this.node_markers[mark] = new OpenLayers.Feature.Vector(this.LonLatToPoint(this.
										   LonLatToM(
										       new OpenLayers.LonLat(lonlat.lon,lonlat.lat))), 
							   mark, 
							   this.icon[mark]
							  );
	this.layerMarkers.addFeatures(this.node_markers[mark]);
	this.layerMarkers.drawFeature(this.node_markers[mark]);
	if( this.areBothMarked() ) { 
            this.compute();
	}
	this.reverseGeocoding(lonlat, mark);
    }, // End of function setMark(lonlat, mark)
    
    areBothMarked: function() {
	return this.nodes['start'] && this.nodes['dest'] && this.nodes['start'].lon && this.nodes['dest'].lat && this.nodes['dest'].lon && this.nodes['dest'].lat; 
    },
    
    addToHash: function() {
	var self = this;
	var tmp = new OpenLayers.LonLat(this.map.center.lon, 
					this.map.center.lat).transform(
					    this.map.getProjectionObject(),
					    this.proj4326); 
	$.getJSON("addhash", {
                      mlon: tmp.lon,
                      mlat: tmp.lat,
                      zoom: self.map.zoom,
                      slon: self.nodes['start'].lon, 
                      slat: self.nodes['start'].lat,
                      dlon: self.nodes['dest'].lon,
                      dlat: self.nodes['dest'].lat,
                      time: $("#time").val(),
                      saddress: $('#startAdr').val(),
                      daddress: $('#endAdr').val()
		  },
		  function(data){
                      if(data.error){
			  $("#hash_url").html('');
                      } else {
			  $("#hash_url").html(
                              "<p>Lien vers cette recherche : <br/><span class=\"tinyText\">" +
				  self.hashUrl + "/h?id="+data.h+"</span></p>"
			  );  
                      }
		  }
		 );
    },
    
    transformToDurationString: function(v) {
	var tmp = parseInt(v);
	var minutes = ( tmp / 60) % 60;
	var hours = tmp / 3600;
	if( (Math.ceil(hours) - 1) > 0 )
            return ( (Math.ceil(hours) - 1) + "h" + (Math.ceil(minutes)) + "min");
	else
            return ( (Math.ceil(minutes) ) + "min");
    },       

    initPosition: function(pos){
	if (this.gpsLayer == undefined){
	    var self=this;
	    $('#startGeo').show().click(function(){self.setDepFromGeo();});
	    $('#destGeo').show().click(function(){self.setDestFromGeo();});

	    var gpsStyleMap = new OpenLayers.StyleMap({'strokeColor': "#204a87",
						       'fillColor': "#729fcf", 
						       'strokeWidth': 1});
	    gpsStyleMap.addUniqueValueRules("default", "name", {'pointer': {graphicWidth: 21,
									    graphicHeight: 21,
									    graphicXOffset: -10,
									    graphicYOffset: -10,
									    graphicOpacity: 1.0,
									    externalGraphic: "/static/img/target.png"},
								'accuracy': {'fillOpacity': 0.2}});

	    this.gpsLayer = new OpenLayers.Layer.Vector("GPS", {styleMap: gpsStyleMap});
	    this.map.addLayer(this.gpsLayer);
	    this.map.setLayerIndex(this.gpsLayer, 1);
	}
    },
    
    refreshPosition: function(pos){
	this.current_position = pos;
	this.initPosition();

	var lonLat = new OpenLayers.LonLat(pos.coords.longitude, 
					   pos.coords.latitude);
	var accuracy = pos.accuracy;
	var mapCoordinate = lonLat.transform(this.proj4326,
 					     this.map.getProjectionObject());
	if(this.node_markers['position']) {
            this.gpsLayer.removeFeatures(this.node_markers['position']);
            this.node_markers['position'].destroy();
            this.node_markers['position'] = null;
	}
	this.node_markers['position'] = new OpenLayers.Feature.
	    Vector(this.LonLatToPoint(mapCoordinate),
		   {'name': 'pointer'});
	this.gpsLayer.addFeatures(this.node_markers['position']);
	this.gpsLayer.drawFeature(this.node_markers['position']);
	
	if (accuracy){
	    if(this.node_markers['position-accuracy']) {
		this.gpsLayer.removeFeatures(this.node_markers['position-accuracy']);
		this.node_markers['position-accuracy'].destroy();
		this.node_markers['position-accuracy'] = null;
	    }
	    this.node_markers['position-accuracy'] = new OpenLayers.Feature.
		Vector(OpenLayers.Geometry.Polygon.
		       createRegularPolygon(this.LonLatToPoint(mapCoordinate),
					    accuracy, 40),
		       {'name':'accuracy'});
	    this.gpsLayer.addFeatures(this.node_markers['position-accuracy']);
	    this.gpsLayer.drawFeature(this.node_markers['position-accuracy']);
	}
    },
    
    hasChanged: function(mark) {
	if( mark == "start" ) {
            var tmp = $('#startAdr').val();
            if( tmp == this.cacheStart){
                return false;
	    }else{
                return true;
	    }
	} else if( mark == "dest" ) {
            var tmp = $('#endAdr').val();
	    if( tmp == this.cacheDest){
                return false;
	    } else {
                return true;
	    }
	} else {
	    return false;
	}
    },
    
    clearPath: function() {
	$("#routing_description").html("");
	$("#info > h2").html("Itinéraires");
	$("#path_costs").html("");
	$("#hash_url").html("");
	this.routeLayer.destroyFeatures();   
    },
    
    clearArrow: function(mark) {
	this.nodes[mark] = null;
	this.layerMarkers.removeFeatures(this.node_markers[mark]);
	this.node_markers[mark].destroy(); 
	this.node_markers[mark] = null;
    },
    
    geocoding: function(str,mark) {
	var url = "geo";
	var self = this;
	$.getJSON(url, {q: str},
		  function(data) {
		      if( data.cord_error != '' ) {
			  if( mark == "start" ) {
                              $('#startAdr').css({backgroundColor: "#f48b5d"});
                              $("#formError_start").html("<span class=\"errorOrange\">Adresse inconnue</span>");
                              self.clearPath();
                              self.clearArrow(mark);
			      
			  } else if( mark == "dest" ) {
                              $('#endAdr').css({backgroundColor: "#f48b5d"});
                              $("#formError_dest").html("<span class=\"errorOrange\">Adresse inconnue</span>");
                              self.clearPath();
                              self.clearArrow(mark);
			  }               
                      }
                      else if( !data.is_covered ) {
			  if( mark == "start" ) {
                              $('#startAdr').css({backgroundColor: "#f48b5d"});
                              $("#formError_start").html("<span class=\"errorOrange\">Ce lieux est trop éloigné de Rennes</span>");
                              self.clearPath();
                              self.clearArrow(mark);
			  }                   
			  else if( mark == "dest" ) {
                              $('#endAdr').css({backgroundColor: "#f48b5d"});
                              $("#formError_dest").html("<span class=\"errorOrange\">Ce lieux est trop éloigné de Rennes</span>");
                              self.clearPath();
                              self.clearArrow(mark);
			  }               
                      }               
                      else if(data.node_error != '') {
			  if(mark == "start"){
                              $('#startAdr').css({backgroundColor: "#f48b5d"});
                              $("#formError_start").html(
				  "<span class=\"errorOrange\">Adresse inconnue</span>"
                              );
                              self.clearPath();
                              self.clearArrow(mark);
			  } else if(mark == "dest") {
                              $('#endAdr').css({backgroundColor: "#f48b5d"});
                              $("#formError_dest").html(
				  "<span class=\"errorOrange\">Adresse inconnue</span>"
                              );
                              self.clearPath();
                              self.clearArrow(mark);
			  }
                      } else {
			  var cord = new OpenLayers.LonLat(data.lon, data.lat);
			  if(mark == "start"){
                              $('#startAdr').val(data.display_name);
			  } else if(mark == "dest") {
			      $('#endAdr').val(data.display_name);			      
			  }
			  if(self.hasChanged(mark)){
                              self.nodes['fmouse_'+mark] = false;      
                              self.nodes[mark] = {
				  'lon': data.lon,
				  'lat': data.lat
                              };                      
                              self.setMark(cord, mark);
                              if(self.areBothMarked()) { 
				  if( !self.nodes['fmouse_start'] || !self.nodes['fmouse_dest'] ) {
                                      self.centerToMap(self.nodes['start'], self.nodes['dest']);
				  }
				  self.compute();
                              }
			  }
                      }
		  }
		 );
    },
    
    validateAddresses: function() {
	$('#startAdr').css({backgroundColor: "#ffffff"});
	$('#endAdr').css({backgroundColor: "#ffffff"});
	if($("#startAdr").val() == '') {
            $('#startAdr').focus();
            $('#startAdr').css({backgroundColor: "#f64444"});
            $("#formError_start").html("<span class=\"errorRed\">Entrez une lieu de départ</span>");
            clearPath();
            clearArrow("start");
	}
	else {
            $('#startAdr').css({backgroundColor: "#ffffff"});
            $("#formError_start").html("");
	}
	if($("#endAdr").val() == '') {
            $('#endAdr').focus();
            $('#endAdr').css({backgroundColor: "#f64444"});
            $("#formError_dest").html("<span class=\"errorRed\">Entrez une destination</span>");
            clearPath();
            clearArrow("dest");
	}
	else {
            $('#endAdr').css({backgroundColor: "#ffffff"});
            $("#formError_dest").html("");
	}
	if( ($("#startAdr").val() != '') && ($("#endAdr").val() != '') ) {
            $('#startAdr').css({backgroundColor: "#ffffff"});
            $('#endAdr').css({backgroundColor: "#ffffff"});
            this.geocoding( $("#startAdr").val(), "start" );
            this.geocoding( $("#endAdr").val(), "dest" );
	    this.compute();
	}
    },
    
    reverseLocations: function() {
	var tmp = $("#startAdr").val();
	$("#startAdr").val($("#endAdr").val());
	$("#endAdr").val(tmp);
	return true;
    },
    
    reverseGeocoding: function(lonlat,mark) {
	var url = "revgeo";
	var self = this;
	$.getJSON(url, {lon: lonlat.lon, lat:lonlat.lat},
		  function(data) {
		      if( data.cord_error != '' ) {
			  if( mark == "start" ) {
                              $('#startAdr').css({backgroundColor: "#f48b5d"});
                              $("#formError_start").html("<span class=\"errorOrange\">Nothing found. Please type again.</span>");
			  }                   
			  else if( mark == "dest" ) {
                              $('#endAdr').css({backgroundColor: "#f48b5d"});
                              $("#formError_dest").html("<span class=\"errorOrange\">Nothing found. Please type again.</span>");
			  }               
                      }
                      else if( !data.is_covered ) {
			  if( mark == "start" ) {
                              $('#startAdr').css({backgroundColor: "#f48b5d"});
                              $("#formError_start").html("<span class=\"errorOrange\">Not in covered zone.</span>");
			  }                   
			  else if( mark == "dest" ) {
                              $('#endAdr').css({backgroundColor: "#f48b5d"});
                              $("#formError_dest").html("<span class=\"errorOrange\">Not in covered zone.</span>");
			  }               
                      }               
                      else if( data.node_error != '' ) {
			  if( mark == "start" ) {
                              $('#startAdr').css({backgroundColor: "#f48b5d"});
                              $("#formError_start").html(
				  "<span class=\"errorOrange\">Can not find a node. Retry with a different address.</span>"
                              );
			  }                   
			  else if( mark == "dest" ) {
                              $('#endAdr').css({backgroundColor: "#f48b5d"});
                              $("#formError_dest").html(
				  "<span class=\"errorOrange\">Can not find a node. Retry with a different address.</span>"
                              );
			  }               
                      }
                      else {              
			  if( mark == "start" ) {
                              $('#startAdr').val(data.display_name);
                              $('#startAdr').css({backgroundColor: "#ffffff"});
                              $("#formError_start").html("");
			  }
			  else if( mark == "dest" ) {
                              $('#endAdr').val(data.display_name);
                              $('#endAdr').css({backgroundColor: "#ffffff"});
                              $("#formError_dest").html("");
			  }
                      }
		  });
    },
    
    centerToMap: function(start,dest) {
	var left,right,top,bottom;  
	var tmps = new OpenLayers.LonLat(start.lon, start.lat).transform(this.proj4326, this.map.getProjectionObject());
	var tmpd = new OpenLayers.LonLat(dest.lon, dest.lat).transform(this.proj4326, this.map.getProjectionObject());
	if( tmps.lon > tmpd.lon) {
            right = tmps.lon;
            left = tmpd.lon;
	}       
	else {
            left = tmps.lon;
            right = tmpd.lon;
	}   
	if( tmps.lat > tmpd.lat) {
            top = tmps.lat;
            bottom = tmpd.lat;  
	}   
	else {
            bottom = tmps.lat;
            top = tmpd.lat;
	}
	this.map.zoomToExtent( new OpenLayers.Bounds( left, bottom, right, top ) );
    },

    secondesToHuman: function(s){
	var hours = Math.floor(s / 3600);
	var minutes = Math.floor((s - (hours * 3600)) / 60);
	return pad(hours) + 'h' + pad(minutes);
    },
 
    LonLatToPoint: function(ll) {
	return new OpenLayers.Geometry.Point(ll.lon,ll.lat);
    },
    
    LonLatToM: function(ll) {
	return ll.transform(this.proj4326,this.proj900913);
    },
    
    MToLonLat: function(ll) {
	return ll.transform(this.proj900913, this.proj4326);
    },
    
    showDescription: function( l ) {
	$("#routing_description").html("<caption><span>Routing description:</span></caption><thread><tr><td><span class=\"tinyText\">Transport</span></td><td><span class=\"tinyText\">Color<span class=\"tinyText\"></td></tr></thread><tbody>");
	$.each( l, function(key, val){
		    $("#routing_description").append("<tr><td><span class=\"tinyText\">" + key + "</span></td><td><hr width=\"60\" size=\"4\" color=\"" + val.strokeColor + "\"></td></tr>");
		});
	$("#routing_description").append("</tbody>");
	
    }
};

$(function(){
      $('#panel-toggle').click(function(){
				   var toggler = this;
				   var w = $('#left-panel').width();
				   var m = toggler.panelHidden ? 0 : -w;
				   var to_pan = (toggler.panelHidden ? -w : w)/2;
				   $('#left-panel').animate({'margin-left': m},
						     {step: function(now,fx){
							  $('#panel-toggle').
							      css({left: w+now});
							  $('#right-panel').
							      css({'margin-left': w+now});
						      },
						      complete: function(){
							  toggler.panelHidden=!toggler.panelHidden;
							  if(toggler.panelHidden){
							      $('#panel-toggle').addClass("hidden");
							  }else{
							      $('#panel-toggle').removeClass("hidden");
							  }
							  $.mumoro.map.pan(to_pan, 0, {animate:false});
						      }});
			       });
      // $('#left-panel').
      // 	  bind('touchstart', 
      // 	       function(evt){
      // 		   var e = evt.originalEvent;
      // 		   if(e.touches.length == 1){
      // 		       var t = e.touches[0];
      // 		       this.scroll_touch_started = true;
      // 		       this.scroll_touch_last_pos = [t.clientX, t.clientY];
      // 		   }
      // 		   return true;
      // });
      // $('#left-panel').
      // 	  bind('touchmove', 
      // 	       function(evt){
      // 		   var e = evt.originalEvent;
      // 		   if(e.touches.length == 1 && this.scroll_touch_started){
      // 		       e.preventDefault();
      // 		       var t = e.touches[0];
      // 		       var last_pos = this.scroll_touch_last_pos;
      // 		       var move = [last_pos[0] - t.clientX, last_pos[1] - t.clientY];
      // 		       this.scroll_touch_last_pos = [t.clientX, t.clientY];
      // 		       this.scrollLeft += move[0];
      // 		       this.scrollTop += move[1];
      // 		       return false;
      // 		   } else {
      // 		       return true;
      // 		   }
      // 	       });
      // $('#left-panel').
      // 	  bind("touchcancel",
      // 	       function(){
      // 		   this.scroll_touch_last_pos = undefined;
      // 		   this.scroll_touch_started = false;
      // 		   return true;
      // 	       });
      // $('#left-panel').
      // 	  bind("touchend",
      // 	       function(evt){
      // 		   evt.originalEvent.preventDefault();
      // 		   this.scroll_touch_last_pos = undefined;
      // 		   this.scroll_touch_started = false;
      // 		   return true;
      // 	       });

      if((navigator.userAgent.match(/iPhone/i)) || (navigator.userAgent.match(/iPod/i))) {
	  $('body').addClass('iphone');
	  if(!window.navigator.standalone){
	      var setOrientation = function() {
		  setTimeout(function() {
				 window.scrollTo(0,1);
			     },100);
		  var orientation = window.orientation;
		  switch(orientation) {
		  case 0:
		  case 180:
		      $('body').removeClass('landscape');
		      $('body').addClass('portrait');
		      break; 
		  case 90:
		  case -90: 
		      $('body').removeClass('portrait');
		      $('body').addClass('landscape');
		      break;
		  }
	      };
	      $(window).load(function () {
				 setOrientation();
			     });
	      $(window).bind('orientationchange', 
			     setOrientation);
	  }
      }
});

// Formate le nombre en ajoutant un zéro s'il est inférieur à 10
function pad(a){
    if (a < 10){
	return "0" + a;
    }else{
	return a;
    }
}

