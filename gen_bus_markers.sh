#!/bin/sh

MARKERS=web/static/img/markers_lignes/
PICTOS=web/static/img/pictos_lignes/21/

for i in $(ls ${PICTOS}); do composite -compose atop -geometry +2+2 ${PICTOS}${i} ${MARKERS}pin-bus.png ${MARKERS}${i}; done

for i in $(seq 1 9); do composite -compose atop -geometry +2+2 ${PICTOS}${i}.png ${MARKERS}pin-bus-square.png ${MARKERS}${i}.png; done

