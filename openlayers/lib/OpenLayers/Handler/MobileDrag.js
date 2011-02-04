/* Copyright (c) 2006-2008 MetaCarta, Inc., published under the Clear BSD
 * license.  See http://svn.openlayers.org/trunk/openlayers/license.txt for the
 * full text of the license. */

/**
 * @requires OpenLayers/Handler.js
 */

/**
 * Class: OpenLayers.Handler.MobileDrag
 * The MobileDrag handler is used to deal with sequences of browser events related
 *     to finger dragging on mobile devices.  The handler is used by controls that 
 *     want to know when a drag sequence begins, when a drag is happening, and when
 *     it has finished.
 *
 * Controls that use the MobileDrag handler typically construct it with callbacks
 *     for 'down', 'move', and 'done'.  Callbacks for these keys are called
 *     when the drag begins, with each move, and when the drag is done.  In
 *     addition, controls can have callbacks keyed to 'up' and 'out' if they
 *     care to differentiate between the types of events that correspond with
 *     the end of a drag sequence.  If no drag actually occurs (no mouse move)
 *     the 'down' and 'up' callbacks will be called, but not the 'done'
 *     callback.
 *
 *     This class is very similar to OpenLayers.Handler.Drag
 *
 * Create a new mobile drag handler with the <OpenLayers.Handler.MobileDrag> constructor.
 *
 * Inherits from:
 *  - <OpenLayers.Handler>
 */

OpenLayers.Handler.MobileDrag = OpenLayers.Class(OpenLayers.Handler, {

    /** 
     * Property: started
     * {Boolean} When a touchstart event is received, we want to record it, but
     *     not set 'dragging' until touchmove events start.
     */
    started: false,
 
    /**
     * Property: stopDown
     * {Boolean} Stop propagation of touch events from getting to listeners
     *     on the same element.  Default is true.
     */
    stopDown: true,

    /** 
     * Property: last
     * {<OpenLayers.Pixel>} The last pixel location of the drag.
     */
    last: null,

    /** 
     * Property: start
     * {<OpenLayers.Pixel>} The first pixel location of the drag.
     */
    start: null,
    
    /**
     * Property: interval
     * {Integer} In order to increase performance, an interval (in 
     *     milliseconds) can be set to reduce the number of drag events 
     *     called. If set, a new drag event will not be set until the 
     *     interval has passed. 
     *     Defaults to 0, meaning no interval. 
     */
    interval: 0,
 
    /**
     * Property: timeoutId
     * {String} The id of the timeout used for the mousedown interval.
     *     This is "private", and should be left alone.
     */
    timeoutId: null,

    counter: 0,

    /**
     * Constructor: OpenLayers.Handler.MobileDrag
     * Returns OpenLayers.Handler.MobileDrag
     *
     * Parameters:
     * control - {<OpenLayers.Control>} The control that is making use of
     *     this handler.
     */
    initialize: function(control, callbacks, options) {
        OpenLayers.Handler.prototype.initialize.apply(this, arguments);
    },

    /**
     * Method: destroy
     */    
    destroy: function() {
        OpenLayers.Handler.prototype.destroy.apply(this, arguments);
    },  

    
    /**
     * Method: down
     * This method is called during the handling of the touchstart event.
     *     Subclasses can do their own processing here.
     *
     * Parameters:
     * evt - {Event} The mouse down event
     */
    down: function(evt) {
    },
    
    /**
     * Method: move
     * This method is called during the handling of the touchmove event.
     *     Subclasses can do their own processing here.
     *
     * Parameters:
     * evt - {Event} The mouse move event
     *
     */
    move: function(evt) {
    },

    scale: function(evt){
    },

    startscale: function(evt){
    },

    /**
     * Method: up
     * This method is called during the handling of the touchend event.
     *     Subclasses can do their own processing here.
     *
     * Parameters:
     * evt - {Event} The mouse up event
     */
    up: function(evt) {
    },

    /**
     * Method: touchstart
     * Handle touchstart events
     *
     * Parameters:
     * evt - {Event} 
     *
     * Returns:
     * {Boolean} Let the event propagate.
     */
     touchstart: function (evt) {
	 if(evt.touches.length == 1){
             evt.preventDefault();
             evt.xy = this.getTouchPosition(evt);
             this.dragging = false;
             this.started = true;
             this.start = evt.xy;
             this.last = evt.xy;
             OpenLayers.Element.addClass(
                 this.map.viewPortDiv, "olDragDown"
             );
             this.down(evt);
             this.callback("down", [evt.xy]);
             if(!this.oldOnselectstart) {
	 	 this.oldOnselectstart = (document.onselectstart) ? document.onselectstart : OpenLayers.Function.True;
	 	 document.onselectstart = OpenLayers.Function.False;
             }
             OpenLayers.Event.stop(evt);
             return false;
	 } else if ((evt.touches.length == 2) && this.scaling){
	     evt.preventDefault();
	     evt.xy = this.getTouchPosition(evt);
	     this.started = true;
	     this.start = evt.xy;
             OpenLayers.Event.stop(evt);
             return false;
	 }
	 return true;
    },


    /**
     * Method: touchmove
     * Handle touchmove events
     *
     * Parameters:
     * evt - {Event} 
     *
     * Returns:
     * {Boolean} Let the event propagate.
     */
    touchmove : function(evt) {
	if(evt.touches.length == 1){
            evt.preventDefault();
            evt.xy = this.getTouchPosition(evt);
            if (this.started && !this.timeoutId && (evt.xy.x != this.last.x || evt.xy.y != this.last.y)) {
		if (this.interval > 0) {
                    this.timeoutId = setTimeout(OpenLayers.Function.bind(this.removeTimeout, this), this.interval);
		}
		this.dragging = true;
		this.move(evt);
		this.callback("move", [evt.xy]);

		if(!this.oldOnselectstart) {
                    this.oldOnselectstart = document.onselectstart;
                    document.onselectstart = OpenLayers.Function.False;
		}
		this.last = evt.xy;
            }
            return false;
	}
	return true;
    },

    /**
     * Method: touchend
     * Handle touchend events
     *
     * Parameters:
     * evt - {Event} 
     *
     * Returns:
     * {Boolean} Let the event propagate.
     */
    touchend: function (evt) {
	if(evt.touches.length == 1 && this.moving && this.started){
	    evt.preventDefault();
	    evt.xy = this.getTouchPosition(evt);
	    var dragged = (this.start != this.last);
	    this.started = false;
	    this.dragging = false;
	    OpenLayers.Element.removeClass(
                this.map.viewPortDiv, "olDragDown"
	    );
	    this.up(evt);
	    this.callback("up", [evt.xy]);
	    if(dragged) {
                this.callback("done", [evt.xy]);
	    }
	    document.onselectstart = this.oldOnselectstart;
            return false;
	}
        return true;
    },

    gesturestart: function(evt){
        this.dragging = false;
	this.scaling = true;
	this.startscale(evt);
	this.callback("startscale", [evt.scale]);
	return false;
    },

    gesturechange: function(evt){
	if(this.scaling && this.started){
	    this.scale(evt);
	    this.callback("scale", [evt.scale]);
	    return false;
	}
	return true;
    },

    gestureend: function(evt){
	if(this.scaling && this.started){
	    this.scale(evt);
	    this.callback("scale", [evt.scale]);
	    this.scaling = false;
	    this.started = false;
	    return false;
	}
	return true;
    },
    
    /**
     * Method: removeTimeout
     * Private. Called by mousemove() to remove the drag timeout.
     */
    removeTimeout: function() {
        this.timeoutId = null;
    },

    /**
     * Method: getTouchPosition
     * 
     * Parameters:
     * evt - {Event} 
     * 
     * Returns:
     * {<OpenLayers.Pixel>} The current xy coordinate of the touch/finger, adjusted
     *                      for offsets, this was taken from OpenLayers.Events and modified.
     *                      TODO: Account for scroll.
     */

    getTouchPosition: function (evt) {
        var element = this.map.viewPortDiv;

        if (!element.lefttop) {
            element.lefttop = [
                (document.documentElement.clientLeft || 0),
                (document.documentElement.clientTop  || 0)
            ];
        }
        if (!element.offsets) {
            element.offsets = OpenLayers.Util.pagePosition(element);
        }
	if(evt.touches.length == 2){
            var ts = evt.touches;
            evt.clientX = (ts[0].pageX + ts[1].pageX)/2;
            evt.clientY = (ts[0].pageY + ts[1].pageY)/2;
	} else {
	    evt.clientX = evt.touches[0].pageX;
            evt.clientY = evt.touches[0].pageY;
	} 
        return new OpenLayers.Pixel(
            evt.clientX - element.offsets[0] - element.lefttop[0], 
            evt.clientY - element.offsets[1] - element.lefttop[1]
        ); 
    },

    /**
     * Method: activate
     * Activate the handler.
     * 
     * Returns:
     * {Boolean} The handler was successfully activated.
     */
    activate: function() {
        if (OpenLayers.Handler.prototype.activate.apply(this, arguments)) {
	    this.dragging = false;
	    this.scaling = false;
            return true;
        }
        return false;
    },
 
    /**
     * Method: deactivate 
     * Deactivate the handler.
     * 
     * Returns:
     * {Boolean} The handler was successfully deactivated.
     */
    deactivate: function() {
        if (OpenLayers.Handler.prototype.deactivate.apply(this, arguments)) {
            this.started = false;
            this.dragging = false;
            this.start = null;
            this.last = null;
            OpenLayers.Element.removeClass(
                this.map.viewPortDiv, "olDragDown"
            );
            return true;
        }
        return false;
    },

    CLASS_NAME: "OpenLayers.Handler.MobileDrag"
});


        
