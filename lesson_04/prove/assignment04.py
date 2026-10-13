"""
Course    : CSE 351
Assignment: 04
Student   : <your name here>

Instructions:
    - review instructions in the course

In order to retrieve a weather record from the server, Use the URL:

f'{TOP_API_URL}/record/{name}/{recno}

where:

name: name of the city
recno: record number starting from 0

"""

import time
from common import *

from cse351 import *

THREADS = 125                 # TODO - set for your program
WORKERS = 10                 # TODO - set for your program
RECORDS_TO_RETRIEVE = 5000  # Don't change


# ---------------------------------------------------------------------------
def retrieve_weather_data(
        command_queue, weather_queue,
        command_slots, command_items, command_lock,
        weather_slots, weather_items, weather_lock):

    while True:
        command_items.acquire()

        with command_lock:
            command = command_queue.get()

        command_slots.release()

        if command is None:
            break

        city, record_number = command

        data = get_data_from_server(
            f'{TOP_API_URL}/record/{city}/{record_number}'
        )

        if data is not None:
            weather_slots.acquire()

            with weather_lock:
                weather_queue.put((
                    data['city'],
                    data['date'],
                    data['temp']
                ))

            weather_items.release()


# ---------------------------------------------------------------------------
class Worker(threading.Thread):

    def __init__(
            self, weather_queue, weather_slots,
            weather_items, weather_lock, noaa):

        super().__init__()
        self.weather_queue = weather_queue
        self.weather_slots = weather_slots
        self.weather_items = weather_items
        self.weather_lock = weather_lock
        self.noaa = noaa

    def run(self):
        while True:
            self.weather_items.acquire()

            with self.weather_lock:
                record = self.weather_queue.get()

            self.weather_slots.release()

            if record is None:
                break

            city, date, temp = record
            self.noaa.add_record(city, date, temp)


# ---------------------------------------------------------------------------
# TODO - Complete this class
class NOAA:

    def __init__(self):
        self.weather = {city: [] for city in CITIES}
        self.lock = threading.Lock()

    def add_record(self, city, date, temp):
        with self.lock:
            self.weather[city].append((date, temp))

    def get_temp_details(self, city):
        with self.lock:
            records = self.weather[city]

            if not records:
                return 0.0

            total = sum(temp for date, temp in records)
            return total / len(records)

# ---------------------------------------------------------------------------
class Queue351():
    """ This is the queue object to use for this class. Do not modify!! """

    def __init__(self):
        self.__items = []
   
    def put(self, item):
        assert len(self.__items) <= 10
        self.__items.append(item)

    def get(self):
        return self.__items.pop(0)

    def get_size(self):
        """ Return the size of the queue like queue.Queue does -> Approx size """
        extra = 1 if random.randint(1, 50) == 1 else 0
        if extra > 0:
            extra *= -1 if random.randint(1, 2) == 1 else 1
        return len(self.__items) + extra


# ---------------------------------------------------------------------------
def verify_noaa_results(noaa):

    answers = {
        'sandiego': 14.5004,
        'philadelphia': 14.865,
        'san_antonio': 14.638,
        'san_jose': 14.5756,
        'new_york': 14.6472,
        'houston': 14.591,
        'dallas': 14.835,
        'chicago': 14.6584,
        'los_angeles': 15.2346,
        'phoenix': 12.4404,
    }

    print()
    print('NOAA Results: Verifying Results')
    print('===================================')
    for name in CITIES:
        answer = answers[name]
        avg = noaa.get_temp_details(name)

        if abs(avg - answer) > 0.00001:
            msg = f'FAILED  Expected {answer}'
        else:
            msg = f'PASSED'
        print(f'{name:>15}: {avg:<10} {msg}')
    print('===================================')


# ---------------------------------------------------------------------------
def main():

    log = Log(show_terminal=True, filename_log='assignment.log')
    log.start_timer()

    noaa = NOAA()

    # Start server
    data = get_data_from_server(f'{TOP_API_URL}/start')

    # Get all cities number of records
    print('Retrieving city details')
    city_details = {}
    name = 'City'
    print(f'{name:>15}: Records')
    print('===================================')
    for name in CITIES:
        city_details[name] = get_data_from_server(f'{TOP_API_URL}/city/{name}')
        print(f'{name:>15}: Records = {city_details[name]['records']:,}')
    print('===================================')

    records = RECORDS_TO_RETRIEVE

    # TODO - Create any queues, semaphores, locks or barriers you need
    # Create queues
    command_queue = Queue351()
    weather_queue = Queue351()

    command_lock = threading.Lock()
    weather_lock = threading.Lock()

    command_slots = threading.Semaphore(10)
    command_items = threading.Semaphore(0)

    weather_slots = threading.Semaphore(10)
    weather_items = threading.Semaphore(0)

    # Start worker threads
    worker_threads = []

    for _ in range(WORKERS):
        worker = Worker(
            weather_queue,
            weather_slots,
            weather_items,
            weather_lock,
            noaa
        )
        worker.start()
        worker_threads.append(worker)

    # Start retrieval threads
    retrieval_threads = []

    for _ in range(THREADS):
        thread = threading.Thread(
            target=retrieve_weather_data,
            args=(
                command_queue,
                weather_queue,
                command_slots,
                command_items,
                command_lock,
                weather_slots,
                weather_items,
                weather_lock
            )
        )
        thread.start()
        retrieval_threads.append(thread)

    # Queue every weather record
    for city in CITIES:
        for record_number in range(records):
            command_slots.acquire()

            with command_lock:
                command_queue.put((city, record_number))

            command_items.release()

    # Stop retrieval threads
    for _ in range(THREADS):
        command_slots.acquire()

        with command_lock:
            command_queue.put(None)

        command_items.release()

    # Wait for retrieval to finish
    for thread in retrieval_threads:
        thread.join()

    # Stop worker threads
    for _ in range(WORKERS):
        weather_slots.acquire()

        with weather_lock:
            weather_queue.put(None)

        weather_items.release()

    # Wait for workers to finish storing records
    for worker in worker_threads:
        worker.join()

    # End server - don't change below
    data = get_data_from_server(f'{TOP_API_URL}/end')
    print(data)

    verify_noaa_results(noaa)

    log.stop_timer('Run time: ')


if __name__ == '__main__':
    main()

