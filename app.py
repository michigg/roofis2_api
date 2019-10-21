from urllib.parse import urlencode, quote_plus

import requests
from flask import Flask, request, jsonify
from flask_caching import Cache

UNIVIS_ROOMS_API = "http://127.0.0.1:5000/api/v1/rooms/"
UNIVIS_ALLOCATION_API = "http://127.0.0.1:5000/api/v1/allocations/"
API_V1_ROOT = "/api/v1/"
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

EXCLUDED_ORGNAMES = ["Fachvertretung für Didaktik der Kunst", "Lehrstuhl für Musikpädagogik und Musikdidaktik",
                     "Bamberg Graduate School of Social Sciences (BAGSS)", "Institut für Psychologie"]
EXCLUDED_ROOM_NAMES = ["Tower Lounge WIAI", "PC-Labor", "PC-Labor 1", "PC-Labor 2", "EFDA", "Dienstzimmer", "Foyer"]


def make_cache_key(*args, **kwargs):
    path = request.path
    args = str(hash(frozenset(request.args.items())))
    return (path + args)


@app.route(f'{API_V1_ROOT}/', methods=['GET'])
def roofis():
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    start_time = request.args.get('start_time', None)
    end_time = request.args.get('end_time', None)
    faculty = request.args.get('faculty', None)
    building_key = request.args.get('building_key', None)
    verbose = request.args.get('verbose', 'True') == "True"

    if start_date and end_date and start_time:
        allocations_url = _get_allocation_url(building_key, end_date, end_time, faculty, start_date, start_time)
        rooms_url = _get_rooms_url(building_key, faculty)
        print(allocations_url)
        print(rooms_url)

        r_allocations = requests.get(allocations_url)
        r_rooms = requests.get(rooms_url)

        if r_allocations.status_code == 200 and r_rooms.status_code == 200:
            allocations = r_allocations.json()
            rooms = r_rooms.json()

            allocated_rooms = []
            for allocation in allocations:
                for room in allocation['rooms']:
                    allocated_rooms.append(room['univis_key'])
            free_rooms = [room for room in rooms if room['univis_key'] not in allocated_rooms and is_excluded(room)]
            if verbose:
                return jsonify(free_rooms)
            else:
                return jsonify(
                    [{'short': f'{room["building_key"]}/{room["floor"]}.{room["number"]}'} for room in free_rooms])
    return jsonify(status_code=400)


def is_excluded(room):
    return room["orgname"] not in EXCLUDED_ORGNAMES and room["name"] not in EXCLUDED_ROOM_NAMES


def _get_allocation_url(building_key=None, end_date=None, end_time=None, faculty=None, start_date=None,
                        start_time=None):
    params = {}
    params['start_date'] = start_date
    params['end_date'] = end_date
    params['start_time'] = start_time
    if end_time:
        params['end_time'] = end_time
    if faculty:
        params['department'] = faculty
    if building_key:
        params['name'] = building_key
    return f'{UNIVIS_ALLOCATION_API}?{urlencode(params, quote_via=quote_plus)}'


def _get_rooms_url(building_key=None, faculty=None):
    params = {}
    if faculty:
        params['department'] = faculty
    if building_key:
        params['token'] = building_key
    return f'{UNIVIS_ROOMS_API}?{urlencode(params, quote_via=quote_plus)}'


@app.route(f'{API_V1_ROOT}/building_keys/', methods=['GET'])
def building_keys():
    return jsonify(status_code=400)


@app.route(f'{API_V1_ROOT}/faculties/', methods=['GET'])
def faculties():
    return jsonify(status_code=400)


if __name__ == '__main__':
    app.run(port=5555)
