


function callGeocodingAPI(str,tp)
{
	if( tp == "start" )	
		geolocalise(str);
	else if( tp == "end" )
		geolocalise(str);
	else
		alert("Error on callGeocodingAPI");
}

function geolocalise(str)
{
	var url = "http://nominatim.openstreetmap.org/search?";
	var email = "odysseas.gabrielides@gmail.com"	;
	$.getJSON(url, {format: "json", polygon: "0", addressdetails: "1", email: email, q: 'allee de brienne, toulouse', json_callback: '?'},
		function(data)
		{
		        if(data.error)
			{
		        	$("#formError").html("Error!");
		        }
			else
			{
				$("#formError").html("jQuery works!");
				
		        }
		});
}

function validateAddresses(f) {
  if(f.startAdr.value == '') {
    alert("Please enter a start location");
  }
  else if(f.endAdr.value == '') {
    alert("Please enter a destination");
  }
  else {
    callGeocodingAPI( f.startAdr.value, "start" );
    callGeocodingAPI( f.endAdr.value, "end" );
  }
  return false;
}

