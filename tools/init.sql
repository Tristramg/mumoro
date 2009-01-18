CREATE TABLE links(id int primary key, source int, target int, geom text, bike bool, bike_r bool, car bool, car_r bool, foot bool, length double);
CREATE TABLE nodes(id int primary key, lon double, lat double);
CREATE INDEX geom_idx on nodes(lat,lon);
