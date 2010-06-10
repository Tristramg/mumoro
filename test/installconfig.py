#MUMORO CONFIGURATION BEFORE INSTALLING

#Database type, choose among : 'sqlite', 'mysql', 'postgres', 'oracle', 'mssql', and 'firebird'
db_type = 'postgres'

#Database connexion URL
#For user oriented databases : 'username:password@host:port/database'
#Port can be excluded (default one depending on db_type will be used) : 'username:password@host/database'
#For SQLiTE : 'file_name.db' for relative path or absolute : '/data/guidage/file_name.db'
db_params = 'postgres:takisthecat@localhost/guidage'


#Load street data from (compressed or not) osm file(s) and apply or not a filter for a smaller region
#-----------------------------------------------------------------------------------------------------
#osm_rennes = import_street_data('/data/guidage/rennes.osm',True,top,left,bottom,right)
#osm_paris = import_street_data('/data/guidage/paris.osm')

#Load bike service from an API URL (Don't forget to add http://) with required valid params (depending on each API)
#------------------------------------------------------------------------------------------------------------------
#bike_rennes = import_bike_service('http://service.bike.fr?key=asjhhhghkf&email=odysseas.gabrielides@gmail.com')

#Load municipal data file (Today supported formats : gtfs and trident.)
#----------------------------------------------------------------------
#municipal_rennes = import_municipal_data( '/data/guidage/rennes.gtfs' )


#Create relevant layers from previously imported data
#----------------------------------------------------
#foot_layer_rennes = load_layer( osm_rennes , "foot", foot )
#car_layer_rennes = load_layer( osm_rennes , "car", car )
#taxi_layer_rennes = load_layer( osm_rennes , "taxi", car )

#municipal_layer_rennes = load_layer( municipal_rennes, "municipal", municipal )

#bike_layer_rennes = load_layer ( bike_rennes, "bike", bike )


#Connect 2 given layers on same nodes with the given cost(s)
#-----------------------------------------------------------
#connect_layers_same_nodes( foot_layer_rennes , car_layer_rennes , cost = cost( duration = 0, mode_change = False ) )
#connect_layers_same_nodes( foot_layer_rennes , taxi_layer_rennes , cost = cost( duration = 0, mode_change = False ) )

#Connect 2 given layers on nodes imported from a list (Returned value from import_bike_service or import_municipal_data) with the given cost(s)
#----------------------------------------------------------------------------------------------------------------------------------------------
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

#Administrator valid email
#-------------------------
#admin_email =

#Website valid URL : 'http://url/' example 'http://mumoro.openstreetmap.fr/'
#---------------------------------------------------------------------------
#web_url =

#Default coordinates for centering the map 
#-----------------------------------------
#Default latitude 
#default_lat =
#Default longitude
#default_lon =
