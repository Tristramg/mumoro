	// Start position for the map (hardcoded here for simplicity)
        var lat=48.11094;
        var lon=-1.68038;
        var zoom=15;
	var map; //complex object of type OpenLayers.Map
        var routeLayer;
        var proj4326 = new OpenLayers.Projection("EPSG:4326"); // longitude/latitude in decimal degrees
        var proj900913 = new OpenLayers.Projection("EPSG:900913"); // Google projection
        var nodes = {
            'start': null,
            'dest': null
        };
        var disableClickEvent = false;
        var markerSize = new OpenLayers.Size(25,35);
        var markerOffset = new OpenLayers.Pixel(-markerSize.w, -markerSize.h);
        var icons = {
            'start': new OpenLayers.Icon('img/arrow-green.png',markerSize,markerOffset),
            'dest': new OpenLayers.Icon('img/arrow-finish.png',markerSize,markerOffset)
	};
	var markers = new OpenLayers.Layer.Markers( "Markers" );
	var node_markers = {
             'start': null,
             'dest': null
         };
	var in_options = {'internalProjection': proj900913,'externalProjection': proj4326};  
	var geojson_reader = new OpenLayers.Format.GeoJSON(in_options);
	var features;
	var paths;
	var iscontext;
	var contextMenu;
	jQuery(document).ajaxError(function(event, request, settings){console.log(event); alert("Error"); });
	OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {                
				defaultHandlerOptions: {
					'single': true,
					'double': false,
					'pixelTolerance': 0,
					'stopSingle': false,
					'stopDouble': false
				},initialize: function(options) {
							this.handlerOptions = OpenLayers.Util.extend(
									{},
									this.defaultHandlerOptions);
							OpenLayers.Control.prototype.initialize.apply(
    									this,
									arguments); 
							this.handler = new OpenLayers.Handler.Click(
    									this,
									{
    										'click': function(e){
											if(disableClickEvent) {disableClickEvent = false;}
											else {createContextMenu(e.xy);}
											}
									},
									this.handlerOptions
							);
				} 

	});

function disp_path(id)
{	
	routeLayer.destroyFeatures();
	features = geojson_reader.read(paths[id]);
	if(features)
		routeLayer.addFeatures(features);
}

function compute()
{
	if(nodes['start'] && nodes['dest'])
	{
		$.getJSON("path", {start: nodes['start'].node, dest: nodes['dest'].node},
		function(data)
		{
		        if(data.error)
			{
		        	$("#path_costs").html("error! " + data.error);
		        }
			else
			{
				$("#path_costs").html("Costs:\n<table id=\"costs_table\" class=\"tablesorter\">\n");
				$("#path_costs table").append("<thead><tr>");
				$.each(data.objectives, function(key, val){$("#path_costs tr").append("<th>"+val+"</th>");});
				$("#path_costs table").append("<tbody>");
		        	$.each( data.paths, function(key, val){
		            	$("#path_costs tbody").append("<tr>");
		            	$.each(val.cost, function(k,v){
								if( k != 0 )
									$("#path_costs tbody tr:last").append("<td>"+v+"</td>");
								else
									$("#path_costs tbody tr:last").append(
										"<td>"+transformToDurationString(v)+"</td>"
									);
								}
					);
		            	$("#path_costs tbody tr:last").click(function(){disp_path(key); 
			    	$("#path_costs tbody tr").removeClass("hl"); 
			    	$(this).addClass("hl"); });});
		        	$("#costs_table").tablesorter();
				paths = data.paths;
				disp_path(0);
			}
		});
	}
}

function handleClick(coord, mark)
{
    var lonlat = map.getLonLatFromViewPortPx(coord);
    lonlat.transform(proj900913, proj4326);
    reverseGeolocalise(lonlat,mark);
    setMark(lonlat,mark);   
}

// Coordinates in 4326 projection (lon/lat)
function setMark(lonlat, mark)
{

	    $.getJSON("match", {lon: lonlat.lon, lat:lonlat.lat}, function(data)
	    {
		    if(data.error) 
		    {
			    $("#"+mark+"_node").html("error! " + data.error);
			    nodes[mark] = null;
			    markers.removeMarker(node_markers[mark]);
			    node_markers[mark].destroy();
			    node_markers[mark] = null;
		    }
		    else 
		    {
			    $("#"+mark+"_node").html(data.node);
			    nodes[mark] = {
			    	'node': data.node,
			    	'lon': lonlat.lon,
			    	'lat': lonlat.lat
			    };
			    if(node_markers[mark])
			    {
			    	markers.removeMarker(node_markers[mark]);
			    	node_markers[mark].destroy();
			    	node_markers[mark] = null;
			    }
                            node_markers[mark] = new OpenLayers.Marker(lonlat.transform(proj4326, proj900913), icons[mark].clone());
			    markers.addMarker(node_markers[mark]);
			    compute();
		    }
            });
} // End of function setMark(lonlat, mark)

function transformToDurationString(v) {
	var tmp = parseInt(v);
	var seconds = tmp % 60;
	var minutes = ( tmp / 60) % 60;
	var hours = tmp / 3600;
	if( hours > 0)
   		return ( (Math.ceil(hours) - 1) + "h" + (Math.ceil(minutes) - 1) + "m" + Math.ceil(seconds) + "s" );
	else
		return ( "00h" + (Math.ceil(minutes) - 1) + "m" + Math.ceil(seconds) + "s" );
}		

function createContextMenu(coordinates){
	if( iscontext == true )
	{
		routeLayer.div.removeChild(contextMenu);
		iscontext = false;
	}	
	else if( iscontext == false )
	{	
		iscontext = true;		
		contextMenu = OpenLayers.Util.createDiv('contextMenu',
							coordinates.offset({x: -1, y: -1}),
							new OpenLayers.Size(95,50),
							'',
							'absolute',
							'0px solid black',
							'visible',
							1.0);
		routeLayer.div.appendChild(contextMenu);	
		var menuStart = OpenLayers.Util.createDiv('menuStart',
							new OpenLayers.Pixel(0,0),
							new OpenLayers.Size(95,25),
							'',
							'static',
							'1px solid black',
							'visible',
							1.0);
		contextMenu.appendChild(menuStart);
		$("#menuStart").css({color: "black", background: "white"});
		//Move Point on ContextMenu -Part
		$("#menuStart").append('&nbsp<img class="smallIcon" src="./img/arrow-green.png"></img>&nbsp<span id="menuTextStart" >set Start</span>');
		$("#menuStart").hover(
			function(){
				$("#menuStart").css({
					'background-color' : '#FEE8C8',
					'font-weight' : 'bold',
					'font-family':'Arial,Helvetica,sans-serif',
					'font-size':'12px'});
			},
			function(){
				$("#menuStart").css({
					color: "black",
					background: "white",
					'font-weight' : 'bold',
					'font-family':'Arial,Helvetica,sans-serif',
					'font-size':'12px'});
			}
		);
		$("#menuStart").click(
			function(){
				handleClick(coordinates, 'start');
				disableClickEvent = true;
				routeLayer.div.removeChild(contextMenu);
				iscontext = false;
			}
		);
		var menuEnd = OpenLayers.Util.createDiv('menuEnd',
							new OpenLayers.Pixel(0,0),
							new OpenLayers.Size(95,25),
							'',
							'static',
							'1px solid black',
							'visible',
							1.0);
		contextMenu.appendChild(menuEnd);
		$("#menuEnd").css({ color: "Black", background: "white", "valign":"middle" });
		//Move Point on ContextMenu -Part
		$("#menuEnd").append('&nbsp<img class="smallIcon" src="./img/arrow-finish.png"></img>&nbsp<span id="menuTextEnd">set End</span>');
		$("#menuEnd").hover(
			function(){ $("#menuEnd").css({'background-color' : '#FEE8C8',
							'font-family':'Arial,Helvetica,sans-serif',
							'font-size':'12px'
							});
				},
			function(){ $("#menuEnd").css({color: "Black",
							 background: "white",
							'font-family':'Arial,Helvetica,sans-serif',
							'font-size':'12px'
							});
				}
		);
		$("#menuEnd").click(
			function(){
				handleClick(coordinates, 'dest');
				disableClickEvent = true;
				routeLayer.div.removeChild(contextMenu);
				iscontext = false;
			}
		);
		$(".smallIcon").css({width: 16, height: 20, "padding-top": "2px"});
		$("#menuTextStart").css({
					height: 18,
					width: 100,
					position: "absolute",
					top:"0.5em",
					left:"2em",
					'font-weight' : 'bold',
					'font-family':'Arial,Helvetica,sans-serif',
					'font-size':'12px'}
		);
		$("#menuTextEnd").css({
					height: 18,
					width: 100,
					position: "absolute",
					top:"2.75em",
					left:"2em",
					'font-weight' : 'bold',
					'font-family':'Arial,Helvetica,sans-serif',
					'font-size':'12px'}
		);
	}
} // End of function createContextMenu(coordinates)

//Initialise the 'map' object
function init() {
	document.getElementById('startAdr').value = "";
	document.getElementById('endAdr').value = "";
	iscontext = false;	
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
		"bike": {strokeColor: '#5a5aea'},
		"foot": {strokeColor: '#f14d4d'},
		"bart": {strokeColor: '#00ff00'},
		"muni": {strokeColor: '#00ffff'},
		"connection": {strokeColor: '#000000', strokeDashstyle: 'dashdot', strokeWidth: 2}
	};
	styleMap.addUniqueValueRules("default", "layer", lookup);
	var bikeLayer = new OpenLayers.Layer.Text( "Bike Stations",{
					location:"./bikes",
					projection: map.displayProjection
					});
	map.addLayer(bikeLayer);	
	routeLayer = new OpenLayers.Layer.Vector("Route", {styleMap: styleMap});
	map.addLayer(routeLayer);
	if( ! map.getCenter() ){
		var lonLat = new OpenLayers.LonLat(lon, lat).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject());
		map.setCenter (lonLat, zoom);
	}
	var click = new OpenLayers.Control.Click();
	map.addControl(click);
	click.activate();
	map.addLayer(markers);
} //End of function init()

function startDrag(feat){
	alert(feat.id);
}

function duringDrag(feat){
	alert(feat.id);
}


