/* Copyright (c) 2006-2008 MetaCarta, Inc., published under the Clear BSD
 * license.  See http://svn.openlayers.org/trunk/openlayers/license.txt for the
 * full text of the license. */

/**
 * @requires OpenLayers/Control.js
 * @requires OpenLayers/Handler/MobileDrag.js
 */

/**
 * Class: OpenLayers.Control.MobileDragPan
 * The MoibleDragPan control pans the map on a mobile device (iPod/iPhone)
 * with your finger. This is an almost exact copy of OpenLayers.Control.DragPan
 *
 * Inherits from:
 *  - <OpenLayers.Control>
 */
OpenLayers.Control.MobileDragPan = OpenLayers.Class(OpenLayers.Control, {

    /** 
     * Property: type
     * {OpenLayers.Control.TYPES}
     */
    type: OpenLayers.Control.TYPE_TOOL,
 
    /**
     * APIProperty: autoActivate
     * {Boolean} Activate the control when it is added to a map.
     */
    autoActivate: true,
   
    /**
     * Property: panned
     * {Boolean} The map moved.
     */
    panned: false,
    
    /**
     * Property: interval
     * {Integer} The number of milliseconds that should ellapse before
     *     panning the map again. Set this to increase dragging performance.
     *     Defaults to 25 milliseconds.
     */
    interval: 25,
    
    /**
     * APIProperty: documentDrag
     * {Boolean} If set to true, mouse dragging will continue even if the
     *     mouse cursor leaves the map viewport. Default is false.
     */
    documentDrag: false,
    
    /**
     * Method: draw
     * Creates a MobileDrag handler, using <panMap> and
     * <panMapDone> as callbacks.
     */    
    draw: function() {
        this.handler = new OpenLayers.Handler.MobileDrag(this, {
                "move": this.panMap,
                "done": this.panMapDone,
                "startscale": this.startScaleMap,
                "scale": this.scaleMap
 
            }, {
                interval: this.interval,
                documentDrag: this.documentDrag
            }
        );
    },

    /**
    * Method: panMap
    *
    * Parameters:
    * xy - {<OpenLayers.Pixel>} Pixel of the mouse position
    */
    panMap: function(xy) {
        this.panned = true;
        this.map.pan(
            this.handler.last.x - xy.x,
            this.handler.last.y - xy.y,
            {dragging: this.handler.dragging, animate: false}
        );
    },
    
    /**
     * Method: panMapDone
     * Finish the panning operation.  Only call setCenter (through <panMap>)
     *     if the map has actually been moved.
     *
     * Parameters:
     * xy - {<OpenLayers.Pixel>} Pixel of the mouse position
     */
    panMapDone: function(xy) {
        if(this.panned) {
            this.panMap(xy);
            this.panned = false;
        }
    },

    startScaleMap: function(scale) {
	this.initialZoom = this.map.getZoom();
    },
							
    scaleMap: function(scale) {
        var newZoom = this.initialZoom * (1 + (scale -1)* 0.2);
        newZoom = Math.max(newZoom, 0);
        newZoom = Math.min(newZoom, this.map.getNumZoomLevels());
        if (newZoom == this.map.getZoom()) {
            return;
        }
        var size    = this.map.getSize();
        var deltaX  = size.w/2 - this.handler.start.x;
        var deltaY  = this.handler.start.y - size.h/2;
        var newRes  = this.map.baseLayer.getResolutionForZoom(newZoom);
        var zoomPoint = this.map.getLonLatFromPixel(this.handler.start);
        var newCenter = new OpenLayers.LonLat(
                            zoomPoint.lon + deltaX * newRes,
                            zoomPoint.lat + deltaY * newRes );
        this.map.setCenter( newCenter, newZoom );
    },

    CLASS_NAME: "OpenLayers.Control.MobileDragPan"
});