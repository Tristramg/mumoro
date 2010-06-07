osm_rennes = load_osm('/data/guidage/rennes.osm',top,left,bottom,right)
osm_paris = load_osm('/data/guidage/paris.osm')

bike_rennes = load_service('http://service.bike.fr?key=asjhhhghkf&email=odysseas.gabrielides@gmail.com')

municipal_rennes = load_municipal( '/data/guidage/rennes.gtfs' )

foot_layer_rennes = load_layer( osm_rennes , "foot", foot )
car_layer_rennes = load_layer( osm_rennes , "car", car )
taxi_layer_rennes = load_layer( osm_rennes , "taxi", car )

municipal_layer_rennes = load_layer( municipal_rennes, "municipal", municipal )

bike_layer_rennes = load_layer ( bike_rennes, "bike", bike )

connect_layers_same_nodes( foot_layer_rennes , car_layer_rennes , cost = cost( duration = 0, mode_change = False ) )
connect_layers_same_nodes( foot_layer_rennes , taxi_layer_rennes , cost = cost( duration = 0, mode_change = False ) )

connect_layers_from_node_list( foot_layer_rennes , 
                                bike_layer_rennes, 
                                bike_rennes , 
                                cost1 = cost( duration = 60, mode_change = True ), 
                                cost2 = cost( duration = 30, mode_change = False ) 
                                )
connect_layers_from_node_list( foot_layer_rennes , 
                                municipal_layer_rennes , 
                                municipal_rennes, 
                                cost1 = cost( duration = 180, mode_change = True ), 
                                cost2 = cost( duration = 180, mode_change = False )
                                )
