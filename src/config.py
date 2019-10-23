import os

BUILDING_KEY_MAP = {"Erba": {'building_keys': ['WE5'], 'geojson_file': ''},
                    "Feki": {'building_keys': ["F21", "FG1", "FG2", "FMA"], 'geojson_file': ''},
                    "Markushaus": {'building_keys': ["M3N", "M3", "MG1", "MG2"], 'geojson_file': ''},
                    "Innenstadt": {'building_keys': ["U2", "U5", "U7"], 'geojson_file': ''}
                    }
EXCLUDED_ORGNAMES = ["Fachvertretung für Didaktik der Kunst", "Lehrstuhl für Musikpädagogik und Musikdidaktik",
                     "Bamberg Graduate School of Social Sciences (BAGSS)", "Institut für Psychologie"]
EXCLUDED_ROOM_NAMES = ["Tower Lounge WIAI", "PC-Labor", "PC-Labor 1", "PC-Labor 2", "EFDA", "Dienstzimmer", "Foyer",
                       "Dienstzimmer Neutestamentliche Wissenschaften", "ehem. Senatssaal",
                       "Sitzungszimmer Dekanat GuK", "WAP-Raum", "Sprachlernstudio", "Besprechungsraum",
                       "Seminar- und Videokonferenzraum", "Prüfungsraum", "Prüfungsraum", "Raum Diathek",
                       "Kartensammlung", "Sekretariat", "Büro Sprachlernstudio", "Dozentenzimmer", "Labor",
                       "Multimedialabor", "Sporthalle", "Multimedialabor",
                       "Lehrstuhl für Englische Literaturwissenschaft/Dienstzimmer", "Besprechungsraum - IADK",
                       "Lernwerkstatt", "Sitzungszimmer Fakultät GuK", "Lehrredaktion", "Arbeits-, und Materialraum",
                       "Sitzungszimmer Fakultät GuK"]
UNIVIS_ROOMS_API = os.environ.get("UNIVIS_ROOM_API")
UNIVIS_ALLOCATION_API = os.environ.get("UNIVIS_ALLOCATION_API")
API_V1_ROOT = "/api/v1/"