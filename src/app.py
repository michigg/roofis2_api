import os

import requests
from flask import Flask, jsonify
from flask_restplus import Api, Resource, reqparse, inputs

import utils

UNIVIS_ROOMS_API = os.environ.get("UNIVIS_ROOM_API")
UNIVIS_ALLOCATION_API = os.environ.get("UNIVIS_ALLOCATION_API")
API_V1_ROOT = "/api/v1/"

app = Flask(__name__)
api = Api(app=app, doc='/docs', version='1.0', title='RooFiS2 API',
          description='Room Finder Service 2 API')

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

roofis_parser = reqparse.RequestParser()
roofis_parser.add_argument('start_date', required=True,
                           type=inputs.regex('^([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))$'),
                           help='date from which free rooms are to be searched for')
roofis_parser.add_argument('start_time', required=True,
                           type=inputs.regex('^(?:[01]\d|2[0123]):(?:[012345]\d)$'),
                           help='time from which free rooms are to be searched for')
roofis_parser.add_argument('min_size', type=int, help='filter room by minumum room size')
roofis_parser.add_argument('location', type=str, help='filter rooms by location')
roofis_parser.add_argument('building_key', type=str, help='filter rooms by building key')


@api.route(f'{API_V1_ROOT}')
class Roofis(Resource):

    @api.doc(parser=roofis_parser)
    def get(self):
        """
        returns a list of rooms that are free
        """

        args = roofis_parser.parse_args()

        start_date = args.get('start_date', None)
        start_time = args.get('start_time', None)
        min_size = args.get('min_size', None)
        location = args.get('location', None)
        building_key = args.get('building_key', None)

        if start_date and start_time:
            allocations_url = utils._get_allocation_url(start_date=start_date, start_time=start_time)
            if not location:
                rooms_url = utils._get_rooms_url(building_keys=[building_key] if building_key else None)
            elif location in BUILDING_KEY_MAP:
                rooms_url = utils._get_rooms_url(building_keys=BUILDING_KEY_MAP[location]['building_keys'])
            else:
                return jsonify(status_code=400)

            r_allocations = requests.get(allocations_url)
            r_rooms = requests.get(rooms_url)

            if r_allocations.status_code == 200 and r_rooms.status_code == 200:
                allocations = r_allocations.json()

                rooms = r_rooms.json()
                allocated_rooms = utils.get_allocated_rooms(allocations)

                rooms = [utils.add_allocations(room, allocated_rooms) for room in rooms]

                free_rooms = [utils.add_allocations(room, allocated_rooms) for room in rooms if
                              not utils.is_currently_allocated(room, start_time) and utils.is_excluded(room, min_size)]
                for room in free_rooms:
                    utils.add_next_allocation(room, start_time)

                free_rooms.sort(key=lambda room: f'{room["building_key"]}/{room["floor"]:02}.{room["number"]:03}')
                return jsonify(free_rooms)
        return jsonify(status_code=400)


@api.route(f'{API_V1_ROOT}locations/')
class LocationList(Resource):
    def get(self):
        """
        returns list of available locations
        """
        locations = [location for location in BUILDING_KEY_MAP]
        return jsonify(locations)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)
