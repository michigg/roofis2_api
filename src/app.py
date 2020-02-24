import datetime

import requests
from flask import Flask, jsonify
from flask_restplus import Api, Resource, reqparse, inputs

import utils
from config import BUILDING_KEY_MAP, API_V1_ROOT, UNI_INFO_API
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
api = Api(app=app, doc='/docs', version='1.0', title='RooFiS2 API',
          description='Room Finder Service 2 API')

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

                # EXTRA API
                self.add_exam_allocations(rooms)

                free_rooms = [utils.add_allocations(room, allocated_rooms) for room in rooms if
                              not utils.is_currently_allocated(room, start_time) and utils.is_excluded(room, min_size)]
                for room in free_rooms:
                    utils.add_next_allocation(room, start_time)

                free_rooms.sort(key=lambda room: f'{room["building_key"]}/{room["floor"]:02}.{room["number"]:03}')
                return jsonify(free_rooms)
        return jsonify(status_code=400)

    def add_exam_allocations(self, rooms):
        if UNI_INFO_API:
            response = requests.get(f'{UNI_INFO_API}exams')
            if response.status_code == 200:
                today = datetime.datetime.now().date()
                exam_rooms = [exam_appointment for exam_appointment in response.json() if
                              datetime.datetime.strptime(exam_appointment["date"], "%Y-%m-%d") == today and
                              exam_appointment["room"]["building_key"]]
                exam_room_keys = [
                    f'{exam_appointment["room"]["building_key"]}/{exam_appointment["room"]["floor"]:02}.{exam_appointment["room"]["number"]:03}'
                    for exam_appointment in exam_rooms]
                for room in rooms:
                    room_short = f'{room["building_key"]}/{room["floor"]:02}.{room["number"]:03}'
                    if room_short in exam_room_keys:
                        self.add_rooms_exam_allocation(exam_rooms, room, room_short)

    def add_rooms_exam_allocation(self, exam_rooms, room, room_short):
        room_exam_allocation = [exam_room for exam_room in exam_rooms if
                                f'{exam_room["room"]["building_key"]}/{exam_room["room"]["floor"]:02}.{exam_room["room"]["number"]:03}' == room_short]
        for allocation in room_exam_allocation:
            if allocation["time"] and allocation["minutes_duration"]:
                start_time = datetime.datetime.strptime(allocation["time"], "%H:%M")
                end_time = start_time + datetime.timedelta(
                    minutes=int(allocation["minutes_duration"]))
                room["allocations"].append(
                    {"start_time": allocation["time"], "end_time": end_time.strftime("%H:%M")})


@api.route(f'{API_V1_ROOT}locations/')
class LocationList(Resource):
    def get(self):
        """
        returns list of available locations
        """
        locations = [location for location in BUILDING_KEY_MAP]
        return jsonify(locations)


@api.route(f'{API_V1_ROOT}openings/')
class LocationList(Resource):
    def get(self):
        """
        returns list of available locations
        """
        locations = [location for location in BUILDING_KEY_MAP]
        return jsonify(locations)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)
