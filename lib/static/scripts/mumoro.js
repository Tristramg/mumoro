function disp_path(id) {	
	showDescription();	
	routeLayer.destroyFeatures();
	features = geojson_reader.read(paths[id]);
	if(features)
		routeLayer.addFeatures(features);
}

function compute() {
	if( areBothMarked() )
	{
		$.getJSON("path", {slon: nodes['start'].lon, 
				slat: nodes['start'].lat,
				dlon: nodes['dest'].lon,
				dlat: nodes['dest'].lat
				},
		function(data) {
		        if(data.error) {
		        	$("#path_costs").html("<span class=\"errorOrange\">No route found</span>");
				clearAll();
				clearArrow("start");
				clearArrow("dest");
		        }
			else {
				$("#path_costs").html("<span class=\"tableDes\">Costs:</span>\n<table id=\"costs_table\" class=\"tablesorter\">\n");
				$("#path_costs table").append("<thead><tr>");
				$.each(data.objectives, function(key, val){$("#path_costs tr").append(
										"<th>"+val+"</th>"
									);});
				$("#path_costs table").append("<tbody>");
		        	$.each( data.paths, function(key, val){
		            	$("#path_costs tbody").append("<tr>");
		            	$.each(val.cost, function(k,v){
						if( k != 0 ) {
							if( parseInt(v) != 0 )
								$("#path_costs tbody tr:last").append("<td><span class=\"tableDes\">"+v+"</span></td>");
							else
								$("#path_costs tbody tr:last").append("<td><span class=\"tableDes\">None</span></td>");
						}
						else {
							$("#path_costs tbody tr:last").append(
										"<td>"+transformToDurationString(v)+"</td>"
							);
						}
					});
		            	$("#path_costs tbody tr:last").click(function(){disp_path(key); 
			    	$("#path_costs tbody tr").removeClass("hl"); 
			    	$(this).addClass("hl"); });});
		        	$("#costs_table").tablesorter();
				paths = data.paths;
				disp_path(0);
				if( !fromHash )
					addToHash();
			}
		});
        }
}

function handleClick(coord, mark) {
	var lonlat = map.getLonLatFromViewPortPx(coord);
	lonlat.transform(proj900913, proj4326);
	nodes['fmouse_'+mark]=true;
	reverseGeocoding(lonlat,mark);
}

// Coordinates in 4326 projection (lon/lat)
function setMark(lonlat, mark)
{
	if(node_markers[mark]) {
		layerMarkers.removeFeatures(node_markers[mark]);
		node_markers[mark].destroy();
		node_markers[mark] = null;
	}
	node_markers[mark] = new OpenLayers.Feature.Vector(LonLatToPoint(LonLatToM(
										new OpenLayers.LonLat(lonlat.lon,lonlat.lat))), 
										mark, 
										icon[mark]
	);
	layerMarkers.addFeatures(node_markers[mark]);
	layerMarkers.drawFeature(node_markers[mark]);
	
} // End of function setMark(lonlat, mark)

function areBothMarked() {
	return nodes['start'] && nodes['dest']; 
}

function addToHash() {
	var tmp = new OpenLayers.LonLat(map.center.lon, map.center.lat).transform(
								map.getProjectionObject(),
								new OpenLayers.Projection("EPSG:4326")
	);						
	$.getJSON("addhash", {
				mlon: tmp.lon,
				mlat: tmp.lat,
				zoom: map.zoom,									
				slon: nodes['start'].lon, 
				slat: nodes['start'].lat,
				dlon: nodes['dest'].lon,
				dlat: nodes['dest'].lat,
				saddress: document.getElementById('startAdr').value,
				daddress: document.getElementById('endAdr').value,
				snode: nodes['start'].node,
				dnode: nodes['dest'].node},
				function(data)
				{
					if(data.error)
					{
						$("#hash_url").html(
						"<span class=\"errorOrange\">Couldn't add the route into the database</span>"
						);
					}
					else
					{
						$("#hash_url").html(
						"<p>Send this url to a friend : <br/><span class=\"tinyText\">" +
						hurl +"h?id="+data.h+"</span></p>"
						);	
					}
				}
	);
}

function transformToDurationString(v) {
	var tmp = parseInt(v);
	var minutes = ( tmp / 60) % 60;
	var hours = tmp / 3600;
	if( (Math.ceil(hours) - 1) > 0 )
   		return ( (Math.ceil(hours) - 1) + "h" + (Math.ceil(minutes)) + "m");
	else
		return ( (Math.ceil(minutes) ) + "m");
}		

//Initialise the 'map' object
function init() {
	document.getElementById('startAdr').value = initialStartText;
	document.getElementById('endAdr').value = initialDestText;
	cacheStart = "";
	cacheDest = "";
	nodes['fmouse_start'] = true;
	nodes['fmouse_dest'] = true;
	map = new OpenLayers.Map ("map",
				[
					new OpenLayers.Control.Navigation(),
					new OpenLayers.Control.PanZoomBar(),
					new OpenLayers.Control.LayerSwitcher(),
					new OpenLayers.Control.MousePosition(),
					new OpenLayers.Control.Attribution()
				],
				{
					maxExtent: new OpenLayers.Bounds(-20037508.34,-20037508.34,20037508.34,20037508.34),
					maxResolution: 156543.0399,
					numZoomLevels: 19,
					units: 'm',
					projection: proj900913,
					displayProjection: proj4326
				}
	);
	// Define the map layer
	// Other defined layers are OpenLayers.Layer.OSM.Mapnik, OpenLayers.Layer.OSM.Maplint and OpenLayers.Layer.OSM.CycleMap
	layerTilesMapnik = new OpenLayers.Layer.OSM.Mapnik("Mapnik");
	map.addLayer(layerTilesMapnik);
	layerTilesCycle = new OpenLayers.Layer.OSM.CycleMap("CycleMap");
	map.addLayer(layerTilesCycle);
	layerTilesAtHome = new OpenLayers.Layer.OSM.Osmarender("Osmarender");
	map.addLayer(layerTilesAtHome);
	var styleMap = new OpenLayers.StyleMap({strokeWidth: 3});
	var lookup = {
		"bike": {strokeColor: '#7373e5'},
		"foot": {strokeColor: '#f14d4d'},
		"foot2": {strokeColor: '#f14d4d'},
    		"car": {strokeColor: '#830531'},
		"star": {strokeColor: '#61bd61'},
		"connection": {strokeColor: '#830531', strokeDashstyle: 'dashdot', strokeWidth: 2}
	};
	styleMap.addUniqueValueRules("default", "layer", lookup);
	routeLayer = new OpenLayers.Layer.Vector("Route", {styleMap: styleMap});
	map.addLayer(routeLayer);
	var bikeLayer = new OpenLayers.Layer.Text( "Bike Stations",{
					location:"./bikes",
					projection: map.displayProjection
					});
	map.addLayer(layerMarkers);
	map.addLayer(bikeLayer);
	if( ! map.getCenter() ){
		var lonLat = new OpenLayers.LonLat(lon, lat).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject());
		map.setCenter (lonLat, zoom);
	}
	controlDrag = new OpenLayers.Control.DragFeature(layerMarkers, {
			'onStart': function(feature) {
				feature.style.graphicOpacity = 0.5;
			},
			'onComplete': function(feature) {
				lonlat = new OpenLayers.LonLat(feature.geometry.x,feature.geometry.y);
				ll = MToLonLat(lonlat);
				feature.style.graphicOpacity = 1.0;
				nodes['fmouse_'+feature.data]=true;
				reverseGeocoding(lonlat,feature.data);
				setMark(lonlat,feature.data);
			}
	});
	map.addControl(controlDrag);
	controlDrag.activate();
	adjustDivsToResolution();
	if( fromHash ) {
		var tmpStart = new OpenLayers.LonLat(lonStart, latStart);
		var tmpDest = new OpenLayers.LonLat(lonDest, latDest);
		nodes['start'] = {
			'node': s_n,
			'lon': lonStart,
			'lat': latStart
		};
		nodes['dest'] = {
			'node': d_n,
			'lon': lonDest,
			'lat': latDest
		};
		setMark(tmpStart,"start");
		setMark(tmpDest,"dest");
		compute();
	}
	$("#map").contextMenu({
		menu: 'myMenu'
	},
		function(action, el, pos) {
			var tmp = {
				'x': pos.x,
			    	'y': pos.y
			};			
			handleClick( tmp, action);
	});
} //End of function init()

function hasChanged(mark) {
	if( mark == "start" ) {
		var tmp = document.getElementById('startAdr').value;
		if( tmp.length == cacheStart.length ) {
			if( tmp == cacheStart)
				return false;
			else
				return true;
		}
		else
			return true;
	}
	else if( mark == "dest" ) {
		var tmp = document.getElementById('endAdr').value;
		if( tmp.length == cacheDest.length ) {
			if( tmp == cachDest)
				return false;
			else
				return true;
		}
		else
			return true;
	}
}

function clearAll() {
	$("#routing_description").html("");
	$("#path_costs").html("");
	$("#hash_url").html("");
	routeLayer.destroyFeatures();	
}

function clearArrow(mark) {
	nodes[mark] = null;
	layerMarkers.removeFeatures(node_markers[mark]);
	node_markers[mark].destroy(); 
	node_markers[mark] = null;
}

function geocoding(str,mark) {
	var url = "geo";
	$.getJSON(url, {q: str},
		function(data) {
				if( data.cord_error != '' ) {
					if( mark == "start" ) {
						document.getElementById('startAdr').style.backgroundColor = "#f48b5d";
						$("#formError_start").html("<span class=\"errorOrange\">Nothing found. Please type again.</span>");
						clearAll();
						clearArrow(mark);
					
					}					
					else if( mark == "dest" ) {
						document.getElementById('endAdr').style.backgroundColor = "#f48b5d";
						$("#formError_dest").html("<span class=\"errorOrange\">Nothing found. Please type again.</span>");
						clearAll();
						clearArrow(mark);
					}				
				}
				else if( !data.is_covered ) {
					if( mark == "start" ) {
						document.getElementById('startAdr').style.backgroundColor = "#f48b5d";
						$("#formError_start").html("<span class=\"errorOrange\">Not in covered zone.</span>");
						clearAll();
						clearArrow(mark);
					
					}					
					else if( mark == "dest" ) {
						document.getElementById('endAdr').style.backgroundColor = "#f48b5d";
						$("#formError_dest").html("<span class=\"errorOrange\">Not in covered zone.</span>");
						clearAll();
						clearArrow(mark);
					}				
				}				
				else if( data.node_error != '' ) {
					if( mark == "start" ) {
						document.getElementById('startAdr').style.backgroundColor = "#f48b5d";
						$("#formError_start").html(
							"<span class=\"errorOrange\">Can not find a node. Retry with a different address.</span>"
						);
						clearAll();
						clearArrow(mark);
					
					}					
					else if( mark == "dest" ) {
						document.getElementById('endAdr').style.backgroundColor = "#f48b5d";
						$("#formError_dest").html(
							"<span class=\"errorOrange\">Can not find a node. Retry with a different address.</span>"
						);
						clearAll();
						clearArrow(mark);
					}				
				}
				else {				
					var cord = new OpenLayers.LonLat(data.lon, data.lat);
					if( mark == "start" )
						document.getElementById('startAdr').value = data.display_name;
					else if( mark == "dest" )
						document.getElementById('endAdr').value = data.display_name;
					if( hasChanged(mark) ) {	
						nodes['fmouse_'+mark] = false;		
						nodes[mark] = {
							'node': data.node,
						    	'lon': data.lon,
						    	'lat': data.lat
						};						
						setMark(cord,mark);
						if( areBothMarked() ) {	
							if( !nodes['fmouse_start'] || !nodes['fmouse_dest'] ) {
								centerToMap(nodes['start'],nodes['dest']);
							}
							compute();
						}
					}
				}
		}
	);
}

function validateAddresses(f) {
	document.getElementById('startAdr').style.backgroundColor = "#ffffff";
	document.getElementById('endAdr').style.backgroundColor = "#ffffff";
	if($("#startAdr").val() == '') {
		document.getElementById('startAdr').focus();
		document.getElementById('startAdr').style.backgroundColor = "#f64444";
		$("#formError_start").html("<span class=\"errorRed\">Enter a starting address</span>");
		clearAll();
		clearArrow("start");
	}
	else {
		document.getElementById('startAdr').style.backgroundColor = "#ffffff";
		$("#formError_start").html("");
	}
	if($("#endAdr").val() == '') {
		document.getElementById('endAdr').focus();
		document.getElementById('endAdr').style.backgroundColor = "#f64444";
		$("#formError_dest").html("<span class=\"errorRed\">Enter a destination</span>");
		clearAll();
		clearArrow("dest");
	}
	else {
  		document.getElementById('endAdr').style.backgroundColor = "#ffffff";
		$("#formError_dest").html("");
	}
  	if( ($("#startAdr").val() != '') && ($("#endAdr").val() != '') ) {
		document.getElementById('startAdr').style.backgroundColor = "#ffffff";
		document.getElementById('endAdr').style.backgroundColor = "#ffffff";
		geocoding( $("#startAdr").val(), "start" );
		geocoding( $("#endAdr").val(), "dest" );
	}
}

function reverseLocations() {
	var tmp = document.getElementById("startAdr").value;
	document.getElementById("startAdr").value = document.getElementById("endAdr").value;
	document.getElementById("endAdr").value = tmp;
	return true;
}

function reverseGeocoding(lonlat,mark) {
	var url = "revgeo";
	$.getJSON(url, {lon: lonlat.lon, lat:lonlat.lat},
		function(data) {
			if( data.cord_error != '' ) {
					if( mark == "start" ) {
						document.getElementById('startAdr').style.backgroundColor = "#f48b5d";
						$("#formError_start").html("<span class=\"errorOrange\">Nothing found. Please type again.</span>");
						clearAll();
						clearArrow(mark);
					
					}					
					else if( mark == "dest" ) {
						document.getElementById('endAdr').style.backgroundColor = "#f48b5d";
						$("#formError_dest").html("<span class=\"errorOrange\">Nothing found. Please type again.</span>");
						clearAll();
						clearArrow(mark);
					}				
				}
				else if( !data.is_covered ) {
					if( mark == "start" ) {
						document.getElementById('startAdr').style.backgroundColor = "#f48b5d";
						$("#formError_start").html("<span class=\"errorOrange\">Not in covered zone.</span>");
						clearAll();
						clearArrow(mark);
					
					}					
					else if( mark == "dest" ) {
						document.getElementById('endAdr').style.backgroundColor = "#f48b5d";
						$("#formError_dest").html("<span class=\"errorOrange\">Not in covered zone.</span>");
						clearAll();
						clearArrow(mark);
					}				
				}				
				else if( data.node_error != '' ) {
					if( mark == "start" ) {
						document.getElementById('startAdr').style.backgroundColor = "#f48b5d";
						$("#formError_start").html(
							"<span class=\"errorOrange\">Can not find a node. Retry with a different address.</span>"
						);
						clearAll();
						clearArrow(mark);
					
					}					
					else if( mark == "dest" ) {
						document.getElementById('endAdr').style.backgroundColor = "#f48b5d";
						$("#formError_dest").html(
							"<span class=\"errorOrange\">Can not find a node. Retry with a different address.</span>"
						);
						clearAll();
						clearArrow(mark);
					}				
				}
				else {				
					var cord = new OpenLayers.LonLat(lonlat.lon, lonlat.lat);
					if( mark == "start" ) {
						document.getElementById('startAdr').value = data.display_name;
						document.getElementById('startAdr').style.backgroundColor = "#ffffff";
						$("#formError_start").html("");
					}
					else if( mark == "dest" ) {
						document.getElementById('endAdr').value = data.display_name;
						document.getElementById('endAdr').style.backgroundColor = "#ffffff";
						$("#formError_dest").html("");
					}
					nodes[mark] = {
						'node': data.node,
						'lon': lonlat.lon,
						'lat': lonlat.lat
					};
					setMark(cord,mark);					
					if( areBothMarked() ) {	
						compute();
					}
				}
		});
}

function centerToMap(start,dest) {
	var left,right,top,bottom;	
	var tmps = new OpenLayers.LonLat(start.lon, start.lat).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject());
	var tmpd = new OpenLayers.LonLat(dest.lon, dest.lat).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject());
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
	map.zoomToExtent( new OpenLayers.Bounds( left, bottom, right, top ) );
}

function LonLatToPoint(ll) {
	return new OpenLayers.Geometry.Point(ll.lon,ll.lat);
}

function LonLatToM(ll) {
	return ll.transform(new OpenLayers.Projection("EPSG:4326"),new OpenLayers.Projection("EPSG:900913"));
}

function MToLonLat(ll) {
	return ll.transform(new OpenLayers.Projection("EPSG:900913"),new OpenLayers.Projection("EPSG:4326"));
}

function adjustDivsToResolution() {
	hmap = $(window).height() / 32;
	hmap = hmap * 21;
	$("#map").height(hmap);
}

function showDescription() {
	$("#routing_description").html(
	"<table><caption><span>Routing description:</span></caption><thread><tr><td><span class=\"tinyText\">Transport mean</span></td><td><span class=\"tinyText\">Color<span class=\"tinyText\"></td></tr></thread><tbody><tr><td><span class=\"tinyText\">Foot</span></td><td><img src='img/desc.foot.png'/></td></tr><tr><td><span class=\"tinyText\">Public bike</span></td><td><img src='img/desc.bike.png'/></td></tr><tr><td><span class=\"tinyText\">Car</span></td><td><img src='img/desc.car.png'/></td></tr><tr><td><span class=\"tinyText\">Municipal transports</span></td><td><img src='img/desc.municipal.png'/></td></tr><tr><td><span class=\"tinyText\">Connection</span></td><td><img src='img/desc.connection.png'/></td></tr></tbody></table>"
);
}

