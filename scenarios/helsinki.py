# MUMORO Scenario configuration
# A scenario consists of:
#    * Some general parameters to get the website running
#    * Setting up the various data imputs you want
#    * Defining a layer for every mean of transport you consider
#    * Connecting together all those layers

#########################
# General configuration #
#########################

# Database type, choose among : 'sqlite', 'mysql', 'postgres', 'oracle', 'mssql', and 'firebird'
# You might need to install the corresponding python module.
# Please read SQLalchemy documentation to know which one 
# Example: db_type = 'sqlite'
db_type = 'sqlite'

# Database connection string
# For sqlite: filename
# For other database: 'username:password@host:port/database'
# Please read SQLAlchemy documentation for more information about the connection string
# Example: db_params = 'data.db'
db_params = 'helsinki.db'

# Administrator's email
# It is required to use the geocoding api from nominatim
# Example: admin_email = 'hello@world.net'
admin_email = 'hello@world.net'

# Website URL
# Example: web_url = 'http://localhost:3000/' 
web_url = 'http://localhost:3000/' 

# Listening port
# Example: listening_port = 3000
listening_port = 3000

# Start date
# It is only used for public transport
# Leave it if you don't plan to use them
# Example: start_date = "20100701"
start_date = "20100701"

# End date
# It is only used for public transport
# Leave it if you don't plan to use them
# Example: end_date = "20100701"
end_date = "20101001"


################
# Data sources #
################

# First we must define where we want our data to come from

# Street data comes from OpenStreetMap.

# You can get data of your region at:
# http://download.geofabrik.de/osm/
# http://downloads.cloudmade.com/
# Use Osmosis if you want to cut the files into a smaller one
#
# Uncompressed or compressed with bzip2 or gzip files are accepted
# Example: streets = import_street_data('/home/ody/Developement/mumoro/greece.osm')
#streets = import_street_data('/home/tristram/finland.osm.bz2')


# Bike Rental Scheme

# Accessing the data differs on every city
# Currently we implement:
#   * VeloStar (Rennes)
#   * JC-Decaux (In most French cities, including Paris)
# Some APIs require a Key
# Example: veloStar = import_bike_service('http://data.keolis-rennes.com/xml/?version=1.0&key=GET_YOUR_OWN_KEY&cmd=getstation&param[request]=all', 'VeloStar')


# Public tranport

# We currently support two file formats:
#    * General Transitfeed Feed Specification (also know as the Google format)
#    * Kalkati used in Helsinki
pt = import_kalkati_data( '/home/tristram/mumoro/lib/LVM.xml', 'Helsinki' )

###################
# Describe layers #
###################
# We create a layer for every mean of transport (foot, bike, public transport, etc.)
# There are two kinds of layers:
#    * Modes that use the street (bike, car, foot)
#    * Modes that have a fixed network (public tranpsport)

# data was defined in the data sources. It must be the result of import_street_data
# name is whatever you want
# mode is one of : Foot, Car, Bike. It will define what streets can be used and at what speed
#foot_layer = street_layer(data = streets, name = 'foot', mode = Foot)
#bike_layer = street_layer(data = streets, name = 'car', mode = Car)
#car_layer = street_layer(data = streets, name = 'bike', mode = Bike)

# Whe also need to create a layer for every public transport network we use
pt_layer = public_transport_layer(data = pt, name = "Public Transport", color="#ff0000")

######################
# Connect the layers #
######################

# You need to describe how you can go from one layer to an other
# We suggest to connect every layer to a pedestrian layer

# Connect two layers at every node (only valid if both layer a built from the same data)
# Otherwise behaviour is unspecified

# The second cost is optional and means that it is not possible to go from the second layer to the first one

# We can leave our bike every where, but not take it back
# It takes 60 seconds to leave the bike
# You won't be able to take it again (there is no connection from foot_layer to bike_layer)
#connect_layers_same_nodes(foot_layer , bike_layer , cost(duration = 60, mode_change = True ))



# If we want to restrict interconnections at some nodes:
# If the second cost is ommited, it will be equal to the first
#   * Bike Hire Scheme : you can only take or leave a bike at specific places
#connect_layers_from_node_list( foot_layer, bike_hire_layer,
#        bike_rennes,
#        cost(duration=120, mode_change=True),
#        cost(duration=60, mode_change=False) )


# If we want to connect every node from the first layer to the closest node of the second layer
# If the second cost is ommited, it will be equal to the first
# Example: public transport
#connect_layers_on_nearest_nodes(pt_layer, foot_layer, cost(duration=120, mode_change=True))


