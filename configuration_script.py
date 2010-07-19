#MUMORO CONFIGURATION BEFORE INSTALLING

#Database type, choose among : 'sqlite', 'mysql', 'postgres', 'oracle', 'mssql', and 'firebird'
#db_type = 'postgres'
db_type = 'sqlite'

#Database connexion URL
#For user oriented databases : 'username:password@host:port/database'
#Port can be excluded (default one depending on db_type will be used) : 'username:password@host/database'
#For SQLiTE : 'file_name.db' for relative path or absolute : '/data/guidage/file_name.db'
#db_params = 'postgres:takisthecat@localhost/guidage'
db_params = '/home/ody/mumoro.ody.latest.db'

#Load street data from (compressed or not) osm file(s)
#-----------------------------------------------------
#osm_greece = import_street_data('/home/ody/Developement/mumoro/greece.osm')
osm_champagne = import_street_data('/home/ody/Developement/mumoro/champagne-ardenne.osm')
#osm_bretagne = import_street_data('/home/ody/Developement/mumoro/bretagne.osm.bz2')

#Load bike service from an API URL (Don't forget to add http://) with required valid params (depending on each API)
#------------------------------------------------------------------------------------------------------------------
bike_rennes = import_bike_service('http://data.keolis-rennes.com/xml/?version=1.0&key=UAYPAP0MHD482NR&cmd=getstation&param[request]=all', 'VeloStar')

#Loads muncipal data file 
#( 3 cases : GTFS format (Call TransitFeed), Trident format (Call Chouette), Other : manual implementation ) and insert muncipal data into database.
#start_date & end_date in this format : 'YYYYMMDD'
#---------------------------------------------------------------------------------------------------------------------------------------------------
#municipal_sf = import_municipal_data( '/home/ody/Developement/mumoro/bart.zip', '20100701', '20101031', 'San Fransisco BART' )

#Create relevant layers from previously imported data (First paramater)
#Second paramater is the name given to this layer
#Third parameter is the layer mode, choose among: mumoro.Foot, mumoro.Bike and mumoro.Car 
#For GTFS Municipal layer dont mention layer mode
#--------------------------------------------------------------------------------------------------------------------------------
foot_champagne = load_layer( osm_champagne, 'foot', mumoro.Foot )
car_champagne = load_layer( osm_champagne, 'car', mumoro.Car )
bike_champagne = load_layer( osm_champagne, 'bike', mumoro.Bike )
#tramway_sf = load_layer( municipal_sf, 'bart' )
#foot_greece = load_layer( osm_greece, 'foot_gr', mumoro.Foot )
#car_greece = load_layer( osm_greece, 'car_gr', mumoro.Car )
#bike_greece = load_layer( osm_greece, 'bike_gr', mumoro.Bike )
#foot_bretagne = load_layer( osm_bretagne, 'foot', mumoro.Foot )
#car_bretagne = load_layer( osm_bretagne, 'car', mumoro.Car )
#bike_bretagne = load_layer( osm_bretagne, 'bike', mumoro.Bike )

#Creates a transit cost variable, including the duration in seconds of the transit and if the mode is changed
#------------------------------------------------------------------------------------------------------------
#cost( duration, mode_changed ):
cost1 = cost( duration = 120, mode_changed = True )
cost2 = cost( duration = 60, mode_changed = False )

#Connect 2 given layers on same nodes with the given cost(s)
#-----------------------------------------------------------
#connect_layers_same_nodes( foot_champagne , car_champagne , cost1 )
#connect_layers_same_nodes( foot_champagne , bike_champagne , cost2  )
#connect_layers_same_nodes( foot_bretagne , car_bretagne , cost1 )
#connect_layers_same_nodes( foot_bretagne , bike_bretagne , cost2  )

#Connect 2 given layers on nodes imported from a list (Returned value from import_bike_service or import_municipal_data) with the given cost(s)
#----------------------------------------------------------------------------------------------------------------------------------------------
#connect_layers_from_node_list( layer1, layer2, node_list, cost, cost2 = None )

#connect_layers_from_node_list( foot_layer_rennes , 
#                                bike_layer_rennes, 
#                                bike_rennes , 
#                                cost1 = cost( duration = 60, mode_change = True ), 
#                                cost2 = cost( duration = 30, mode_change = False ) 
#)

#connect_layers_from_node_list( foot_layer_rennes , 
#                                municipal_layer_rennes , 
#                                municipal_rennes, 
#                                cost1 = cost( duration = 180, mode_change = True ), 
#                                cost2 = cost( duration = 180, mode_change = False )
#)

#Connect 2 given layers on nearest nodes
#----------------------------------------
#connect_layers_on_nearest_nodes( layer1 , layer2, cost )
#connect_layers_on_nearest_nodes( foot_champagne, tramway_sf, cost1 )
#connect_layers_on_nearest_nodes( foot_layer_rennes , 
#                                bike_layer_rennes, 
#                                cost = cost( duration = 60, mode_change = True )
#)

#Administrator valid email
#-------------------------
admin_email = 'odysseas.gabrielides@gmail.com'

#Website valid URL : 'http://url/' example 'http://mumoro.openstreetmap.fr/'
#---------------------------------------------------------------------------
web_url = 'http://mumoro.openstreetmap.fr'

#Default coordinates for centering the map 
#-----------------------------------------
#Default latitude 
default_lat = 48.11094
#Default longitude
default_lon = -1.68038

#Listening port
#---------------
listening_port = 3000
