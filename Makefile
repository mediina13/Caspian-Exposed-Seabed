PY ?= python

.PHONY: all exposure accuracy extended map studyarea workflow test clean

all: exposure accuracy extended map

exposure:      ## exposure by year and zone, sea-level link, vegetation, sensitivity
	$(PY) analysis/01_exposure_and_sea_level.py

accuracy:      ## accuracy assessment from the 150 reference points
	$(PY) analysis/02_accuracy.py

extended:      ## long-term record, retreat, protected areas, population, depth test
	$(PY) analysis/03_extended.py

map:           ## before/after map figure
	$(PY) analysis/04_map_figure.py

studyarea:     ## study area map (needs basemap and basemap-data-hires)
	$(PY) analysis/05_study_area_map.py

workflow:      ## workflow diagram
	$(PY) analysis/06_workflow_diagram.py

test:          ## check the headline numbers
	$(PY) -m pytest -q

clean:
	rm -f results/tables/* results/figures/*
