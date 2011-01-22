/* touch.js
 * from: http://docs.opengeo.org/demo/OL/ (whit)
 * cleaned up by: Anders Brownworth http://anders.com/
 * ommented out "event.preventDefault()" for OpenLayers-PopUp-Feature support by: Julian from Germany
 */

TouchHandler = OpenLayers.Class( {
    touchStartX: null,
    touchStartY: null,
    scale: 1,
    skip:1,
    limitPansPerMove: 2,

    /*
     * parameters
     * limitPansPerMove - {Number} experimenting if we can less jerky panning by
     * limiting the number of pan calls. the higher the number the more pan calls skipped.  
     */

    initialize: function( map, limitPansPerMove ) {
	    this.map = map;
	    console.log( "limitPansPerMove " + limitPansPerMove );
	    if ( limitPansPerMove ) {
        	console.log("no  " + limitPansPerMove);
        	this.limitPansPerMove = limitPansPerMove;

	    }

	    // monkey-p map to include limitZoomOut
	    map.constructor.prototype['limitZoomOut'] = function( ) {
            if ( this.getZoom( ) <= 2 ) {
                return true;

            }
            return false;

	    };
	    this.hook_touch( map );
	},

    touchstart: function( ) {
	    var inDoubleTap = false;
	    var doubleTapTimer = false;
	    var zoom = null;

	    var obj = this;
	    return function ( event ) {
        	dec_debug(event);
		//event.preventDefault( );
		if ( event.touches.length == 1 ) {
		    if ( !doubleTapTimer ) {
			doubleTapTimer = setTimeout( function( ) { inDoubleTap = false;
								   doubleTapTimer = false; },
			    500 );
		    }

		    if ( !inDoubleTap ) {
			inDoubleTap = true;

		    }
		    else {
			inDoubleTap = false;
			var out = "out";
			if ( zoom == null || zoom == out ) {
			    obj.map.zoomIn( );
			    zoom = "in";

			}
			else {
			    obj.map.zoomOut( );
			    zoom = out;

			}

		    }

		    var touch = event.touches[0];
		    obj.touchStartX = touch.clientX;
		    obj.touchStartY = touch.clientY;

		    if ( touch.target.width === 128 ) {
			return false;

		    }
		    else {
			return true;

		    }

		};
		return null;

	    };

	},

    pan_touch: function ( ) {
	    var obj = this;
	    return function ( e ) {
        	dec_debug( event );
		e.preventDefault( );
		if ( e.touches.length == 1 ) {
		    var touch = e.touches[0];
		    //hack - limit number of calls to pan
		    if ( obj.skip++ % obj.limitPansPerMove === 0 ) {
            		obj.map.pan( obj.touchStartX - touch.clientX, obj.touchStartY - touch.clientY );

            	}

            }

        };

    },

    zoom_guesture: function( ) {
	    var obj = this;
	    return function ( e ) {
        	dec_debug( event );
		e.preventDefault( );
		if ( e.scale > 1 && e.scale != obj.scale ) {
		    //	if ( this.map.limitZoomIn( ) == false ) {
		    obj.map.zoomIn( );
		    //	}

		}
		else {
		    if ( e.scale < 1 && e.scale != obj.scale ) {
			if ( obj.map.limitZoomOut( ) == false ) {
			    obj.map.zoomOut( );

			}

		    }

		}
		obj.scale = e.scale;

	    };

	},

    hook_touch: function ( ){
	    var map = this.map;
	    map.div.addEventListener("touchstart", this.touchstart(), false);
	    map.div.addEventListener("touchmove", this.pan_touch(), false);
	    map.div.addEventListener("touchend", this.zoom_guesture(), false);
	    map.div.addEventListener("guestureend", this.zoom_guesture(), false);

	}

    } );

// debugging
function repmsg( id, msg ) {
    node = document.getElementById(id);
    if ( node != null )
	node.innerHTML = msg;

};

function dec_debug( event ) {
    repmsg( 'debug', event.type + ' ' + xystr( event ) );

};

function xystr( event ) {
    var coords = " ";
    for ( i = 0; i < event.touches.length; i = i + 1 ) {
        coords = coords + " x:" + event.touches[i].pageX + " y:" + event.touches[i].pageY;

    };
    coords = coords + " s:" + event.scale + " r:" + event.rotation;
    return coords;

};
