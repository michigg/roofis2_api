import time
from urllib.parse import urlencode, quote_plus

from config import EXCLUDED_ORGNAMES, EXCLUDED_ROOM_NAMES, UNIVIS_ROOMS_API, UNIVIS_ALLOCATION_API


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
    room['allocations'] = allocations[room['univis_key']]['allocations'] if room['univis_key'] in allocations else []
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
            if 'next_allocation' in room:
                current_next_allocation = time.strptime(room['next_allocation'], "%H:%S")
                if current_next_allocation.tm_hour > start_time.tm_hour:
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
