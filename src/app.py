import os
import time
from pprint import pprint
from urllib.parse import urlencode, quote_plus

import requests
from flask import Flask, request, jsonify
from flask_caching import Cache

UNIVIS_ROOMS_API = os.environ.get("UNIVIS_ROOM_API")
UNIVIS_ALLOCATION_API = os.environ.get("UNIVIS_ALLOCATION_API")
API_V1_ROOT = "/api/v1/"

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

BUILDING_KEY_MAP = {"Erba": ['WE5'], "Feki": ["F21", "FG1", "FG2", "FMA"], "Markushaus": ["M3N", "M3", "MG1", "MG2"],
                    "Innenstadt": ["U2", "U5", "U7"]}

EXCLUDED_ORGNAMES = ["Fachvertretung für Didaktik der Kunst", "Lehrstuhl für Musikpädagogik und Musikdidaktik",
                     "Bamberg Graduate School of Social Sciences (BAGSS)", "Institut für Psychologie"]
EXCLUDED_ROOM_NAMES = ["Tower Lounge WIAI", "PC-Labor", "PC-Labor 1", "PC-Labor 2", "EFDA", "Dienstzimmer", "Foyer",
                       "Dienstzimmer Neutestamentliche Wissenschaften", "ehem. Senatssaal",
                       "Sitzungszimmer Dekanat GuK", "WAP-Raum", "Sprachlernstudio", "Besprechungsraum",
                       "Seminar- und Videokonferenzraum", "Prüfungsraum", "Prüfungsraum", "Raum Diathek",
                       "Kartensammlung", "Sekretariat", "Büro Sprachlernstudio", "Dozentenzimmer", "Labor",
                       "Multimedialabor", "Sporthalle", "Multimedialabor",
                       "Lehrstuhl für Englische Literaturwissenschaft/Dienstzimmer", "Besprechungsraum - IADK",
                       "Lernwerkstatt"]


def make_cache_key(*args, **kwargs):
    path = request.path
    args = str(hash(frozenset(request.args.items())))
    return (path + args)


@app.route(f'{API_V1_ROOT}/', methods=['GET'])
def roofis():
    start_date = request.args.get('start_date', None)
    start_time = request.args.get('start_time', None)
    min_size = request.args.get('min_size', None)
    location = request.args.get('location', None)
    building_key = request.args.get('building_key', None)

    if start_date and start_time:
        allocations_url = _get_allocation_url(start_date=start_date, start_time=start_time)
        if not location:
            rooms_url = _get_rooms_url(building_keys=[building_key] if building_key else None)
            print(rooms_url)
        elif location in BUILDING_KEY_MAP:
            rooms_url = _get_rooms_url(building_keys=BUILDING_KEY_MAP[location])
        else:
            return jsonify(status_code=400)

        r_allocations = requests.get(allocations_url)
        r_rooms = requests.get(rooms_url)

        if r_allocations.status_code == 200 and r_rooms.status_code == 200:
            allocations = r_allocations.json()
            rooms = r_rooms.json()

            allocated_rooms = get_allocated_rooms(allocations)
            rooms = [add_allocations(room, allocated_rooms) for room in rooms]
            free_rooms = [add_allocations(room, allocated_rooms) for room in rooms if
                          not is_currently_allocated(room, start_time) and is_excluded(room, min_size)]
            for room in free_rooms:
                add_next_allocation(room, start_time)
            return jsonify(free_rooms)
    return jsonify(status_code=400)


def get_allocated_rooms(allocations):
    allocated_rooms = {}
    for allocation in allocations:
        for room in allocation['rooms']:
            if room['univis_key'] not in allocated_rooms or 'allocations' not in allocated_rooms[
                room['univis_key']]:
                allocated_rooms[room['univis_key']] = {}
                allocated_rooms[room['univis_key']]['allocations'] = [allocation]
            else:
                allocated_rooms[room['univis_key']]['allocations'].append(allocation)
    return allocated_rooms


def add_allocations(room, allocations):
    if room['univis_key'] in allocations:
        room['allocations'] = allocations[room['univis_key']]['allocations']
    else:
        room['allocations'] = []
    return room


def is_excluded(room, min_size):
    if min_size:
        return room["orgname"] not in EXCLUDED_ORGNAMES and room["name"] not in EXCLUDED_ROOM_NAMES and room["name"] and \
               room['size'] >= int(min_size)
    return room["orgname"] not in EXCLUDED_ORGNAMES and room["name"] not in EXCLUDED_ROOM_NAMES and room["name"]


def is_currently_allocated(room, start_time):
    requested_start_time = time.strptime(start_time, "%H:%S")
    for allocation in room['allocations']:
        start_time = time.strptime(allocation['start_time'], "%H:%S")
        end_time = time.strptime(allocation['end_time'], "%H:%S")
        if start_time.tm_hour <= requested_start_time.tm_hour < end_time.tm_hour:
            return True
    return False


def add_next_allocation(room, start_time):
    requested_start_time = time.strptime(start_time, "%H:%S")
    for allocation in room['allocations']:
        start_time = time.strptime(allocation['start_time'], "%H:%S")
        if requested_start_time.tm_hour < start_time.tm_hour:
            pprint(f'{start_time.tm_hour} > {requested_start_time.tm_hour}')
            if 'next_allocation' in room:
                current_next_allocation = time.strptime(room['next_allocation'], "%H:%S")
                if current_next_allocation.tm_hour < start_time.tm_hour:
                    room['next_allocation'] = time.strftime("%H:%S", start_time)
            else:
                room['next_allocation'] = time.strftime("%H:%S", start_time)
    return None


def _get_allocation_url(building_key=None, end_date=None, end_time=None, faculty=None, start_date=None,
                        start_time=None):
    params = {}
    params['start_date'] = start_date
    params['end_date'] = end_date if end_date else start_date
    params['start_time'] = start_time
    if faculty:
        params['department'] = faculty
    if building_key:
        params['name'] = building_key
    return f'{UNIVIS_ALLOCATION_API}?{urlencode(params, quote_via=quote_plus)}'


def _get_rooms_url(building_keys=None, faculty=None):
    params = {}
    if faculty:
        params['department'] = faculty
    if building_keys:
        params['building_keys'] = building_keys
    return f'{UNIVIS_ROOMS_API}?{urlencode(params, True, quote_via=quote_plus)}'


@app.route(f'{API_V1_ROOT}/building_keys/', methods=['GET'])
def building_keys():
    return jsonify(status_code=400)


@app.route(f'{API_V1_ROOT}/faculties/', methods=['GET'])
def faculties():
    return jsonify(status_code=400)


@app.route(f'{API_V1_ROOT}locations/', methods=['GET'])
def locations():
    locations = [location for location in BUILDING_KEY_MAP]
    return jsonify(locations)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)
