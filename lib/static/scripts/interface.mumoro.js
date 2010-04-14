function geolocalise(str,mark)
{
	var url = "http://nominatim.openstreetmap.org/search?";
	var email = "odysseas.gabrielides@gmail.com"	;
	$.getJSON(url, {format: "json", polygon: "0", addressdetails: "1", email: email, q: str, json_callback: '?'},
		function(data)
		{
		        if(data.error)
		        	$("#formError").html("    Geocoding error");
		        else
			{
				if( data[0] == null )
				{
					$("#formError").html("    Nothing found");
					if( mark == "start" )
						document.getElementById('startAdr').style.backgroundColor = "#f48b5d";
					else if( mark == "dest" )
						document.getElementById('endAdr').style.backgroundColor = "#f48b5d";
				
				}
				else
				{				
					var cord = new OpenLayers.LonLat(data[0].lon, data[0].lat);
					if( mark == "start" )
						document.getElementById('startAdr').value = data[0].display_name;
					else if( mark == "dest" )
						document.getElementById('endAdr').value = data[0].display_name;
					markArrowsFromCord(cord,mark);
				}
		        }
		}
	);
}

function validateAddresses(f) {
	document.getElementById('startAdr').style.backgroundColor = "#ffffff";
	document.getElementById('endAdr').style.backgroundColor = "#ffffff";
	if(f.startAdr.value == '') {
		document.getElementById('startAdr').focus();
		document.getElementById('startAdr').style.backgroundColor = "#ea7171";
	}
	else
		document.getElementById('startAdr').style.backgroundColor = "#ffffff";
	if(f.endAdr.value == '') {
		document.getElementById('endAdr').focus();
		document.getElementById('endAdr').style.backgroundColor = "#ea7171";
	}
	else
  		document.getElementById('endAdr').style.backgroundColor = "#ffffff";
  	if( (f.startAdr.value != '') && (f.endAdr.value != '') )
	{
		document.getElementById('startAdr').style.backgroundColor = "#ffffff";
		document.getElementById('endAdr').style.backgroundColor = "#ffffff";
		geolocalise( f.startAdr.value, "start" );
		geolocalise( f.endAdr.value, "dest" );
	}
	$("#formError").html("");	
	return false;
}

function markArrowsFromCord(lonlat, mark)
{
	if( (lonlat.lon <= -1.73113) || (lonlat.lon >= -1.56359) || (lonlat.lat <= 48.07448) || (lonlat.lat >= 48.14532) )
	{
		$("#formError").html("    Outside the coverage area");
	 	if( mark == "start" )
			document.getElementById('startAdr').style.backgroundColor = "#f48b5d";
		else if( mark == "dest" )
			document.getElementById('endAdr').style.backgroundColor = "#f48b5d";
	}
}

function reverseLocations()
{
	var tmp = document.getElementById("startAdr").value;
	document.getElementById("startAdr").value = document.getElementById("endAdr").value;
	document.getElementById("endAdr").value = tmp;
	return true;
}

function clearAll()
{
	
}

function reverseGeolocalise(lonlat,mark)
{
	var url = "http://nominatim.openstreetmap.org/reverse?";
	var email = "odysseas.gabrielides@gmail.com"	;
	$.getJSON(url, {format: "json", zoom: "18", addressdetails: "1", lon: lonlat.lon, lat:lonlat.lat, email: email, json_callback: '?'},
		function(data)
		{
			if(data.error)
		        	$("#formError").html("    Reverse geocoding error");
		        else
			{
				if( data.display_name == null )
				{
					$("#formError").html("    Nothing found");
					if( mark == "start" )
						document.getElementById('startAdr').style.backgroundColor = "#f48b5d";
					else if( mark == "dest" )
						document.getElementById('endAdr').style.backgroundColor = "#f48b5d";
				}
				else
				{				
					if( mark == "start" )
					{
						document.getElementById('startAdr').value = data.display_name;
						document.getElementById('startAdr').style.backgroundColor = "#ffffff";
					}
					else if( mark == "dest" )
					{
						document.getElementById('endAdr').value = data.display_name;
						document.getElementById('endAdr').style.backgroundColor = "#ffffff";
					}
					markArrowsFromCord(cord,mark);
				}
		        }
		});
}


