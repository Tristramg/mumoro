#MUMORO CONFIGURATION BEFORE LAUNCHING SERVER

#Database type, choose among : 'sqlite', 'mysql', 'postgres', 'oracle', 'mssql', and 'firebird'
db_type = 'sqlite'

#Database connexion URL
#For user oriented databases : 'username:password@host:port/database'
#Port can be excluded (default one depending on db_type will be used) : 'username:password@host/database'
#For SQLiTE : 'file_name.db' for relative path or absolute : '/data/guidage/file_name.db'
db_params = "sf.db"
#Load street data from (compressed or not) osm file(s)
#-----------------------------------------------------
osm_california = import_street_data("/home/tristram/osmosis-0.35/sf.osm.bz2")

#Load bike service from an API URL (Don't forget to add http://) with required valid params (depending on each API)
#------------------------------------------------------------------------------------------------------------------

#Loads muncipal data file and inserts it into database.
#starting_date & end_date in this format : 'YYYYMMDD' Y for year's digists, M for month's and D for day's
#starting_date and end_date MUST be defined if municipal data is imported
#------------------------------------------------------------------------------------------------------------------
start_date = '20100701'
end_date = '20101231'

bart_sf_data = import_gtfs_data( "/home/tristram/mumoro/bart.zip", 'San Fransisco BART' )
#muni_sf_data = import_municipal_data( '/home/ody/Developement/mumoro/sf.muni.zip', 'San Fransisco Municipal' )

#Create relevant layers from previously imported data (origin paramater) with a name, a color and the mode.
#Color in the html format : '#RRGGBB' with R, G and B respetcly reg, green and blue values in hex
#Mode choose among: mumoro.Foot, mumoro.Bike and mumoro.Car 
#For GTFS Municipal layer dont mention layer mode
#--------------------------------------------------------------------------------------------------------------------
foot_california = street_layer( data = osm_california, name = 'Foot', color = '#7E2217', mode = Foot )
#car_california = street_layer( data = osm_california, name = 'Car', color = '#842DCE', mode = Car )
bart_sf = public_transport_layer( data = bart_sf_data, name = 'BART', color = '#4CC417' )
#muni_sf = load_layer( origin = muni_sf_data, name = 'Municipal', color = '#817339' )


#Starting layer is the layer on wich the route begins
#Destination layer is the layer on wich the route finishes
#Starting & destination layers MUST be selected, otherwise the server could not start
#If by mistake you select more than one starting/destination layers, the affectation will go on the last one
set_starting_layer( foot_california )
set_destination_layer( foot_california )

#Creates a transit cost variable, including the duration in seconds of the transit and if the mode is changed (True or False)
#------------------------------------------------------------------------------------------------------------
cost1 = cost( duration = 120, mode_change = True )
cost2 = cost( duration = 60, mode_change = False )

#Connect 2 given layers on same nodes with the given cost(s)
#-----------------------------------------------------------
#connect_layers_same_nodes( foot_california , car_california , cost1 )

#Connect 2 given layers on nodes imported from a list (Returned value from import_bike_service or import_municipal_data) with the given cost(s)
#----------------------------------------------------------------------------------------------------------------------------------------------
connect_layers_from_node_list( foot_california, bart_sf, bart_sf, cost1, cost2 )
#connect_layers_from_node_list( foot_california, muni_sf, muni_sf, cost1, cost2 )

#Connect 2 given layers on nearest nodes
#----------------------------------------
#connect_layers_on_nearest_nodes( bart_sf, muni_sf, cost1 )

#Administrator valid email
#REQUIRED for geocoding services, if empty the service will NOT work
#-------------------------
admin_email = 'odysseas.gabrielides@gmail.com'

#Website valid URL : 'http://url/' example 'http://mumoro.openstreetmap.fr/'
#REQUIRED for urls generating (allowing you to send the url to a friend and to find the same route)
#---------------------------------------------------------------------------
web_url = 'http://localhost:3002/' 

#Listening port
#Check that it is free and port-fordwarded if behind a router
#---------------
listening_port = 3002
