#Loads an osm (compressed of not) file and insert data into database.Optional : can filter a region with top,left,bottom and right arguments.
import_street_data( file, filter = False, top = 0.0, left = 0.0, bottom = 0.0, right = 0.0 )

#Loads a bike service API ( from already formatted URL ). Insert bike stations in database and enables schedulded re-check.
import_bike_service( url )

#Loads muncipal data file 
#( 3 main cases : GTFS format (Call TransitFeed), Trident format (Call Chouette), Other : manual implementation ) and insert muncipal data into database.
import_municipal_data( file )

#Loads data from previous inserted data and creates a layer used in multi-modal graph
load_layer( data, layer_name, layer_mode )

#Creates a transit cost variable, including the duration in seconds of the transit and if the mode is changed
cost( duration, mode_changed )

#Connects 2 given layers on same nodes with the given cost(s)
connect_layers_same_nodes( layer1, layer2, cost, cost2 = 0 )

#Connect 2 given layers on a node list (arg 3 which should be the returned data from import_municipal_data or import_bike_service) with the given cost(s)
connect_layers_from_node_list( layer1, layer2, node_list, cost, cost2 = 0 ) 
