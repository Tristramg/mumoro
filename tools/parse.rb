require 'rexml/document'

include REXML

file = File.new("velouse.xml")
doc = Document.new(file)
root = doc.root

puts "DROP TABLE velouse;"
puts "CREATE TABLE velouse (lon double, lat double);"
root.each_element('//marker') do |m|
   puts "INSERT INTO velouse (lon, lat) VALUES(#{m.attributes['lng']}, #{m.attributes['lat']});" 
end
