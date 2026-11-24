
"""
Course: CSE 351, week 10
File: functions.py
Author: Your Name

Instructions:

Depth First Search
https://www.youtube.com/watch?v=9RHO6jU--GU

Breadth First Search
https://www.youtube.com/watch?v=86g8jAQug04


Requesting a family from the server:
family_id = 6128784944
data = get_data_from_server('{TOP_API_URL}/family/{family_id}')

Example JSON returned from the server
{
    'id': 6128784944,
    'husband_id': 2367673859,
    'wife_id': 2373686152,
    'children': [2380738417, 2185423094, 2192483455]
}

Requesting an individual from the server:
person_id = 2373686152
data = get_data_from_server('{TOP_API_URL}/person/{person_id}')

--------------------------------------------------------------------------------------
Describe how to speed up part 1:

DFS uses recursion to explore the family tree. I use multiple
threads to retrieve parent families concurrently. I also retrieve
the husband, wife, and children concurrently using a thread pool.
Sets prevent duplicate family and person requests.

Describe how to speed up part 2:

BFS uses a queue-like list to process one generation at a time.
I use a thread pool to retrieve families and individuals concurrently.
A visited set prevents duplicate requests and improves performance.

Extra (Optional) 10% Bonus:

The bonus BFS implementation uses ThreadPoolExecutor with
max_workers=5 to limit concurrent requests to five threads.
"""

from common import *
import queue
import threading
from concurrent.futures import ThreadPoolExecutor


# -----------------------------------------------------------------------------
def depth_fs_pedigree(family_id, tree):
    # Depth First Search using recursion and concurrent requests.

    visited_families = set()
    visited_people = set()
    lock = threading.Lock()

    def get_family(fid):
        for attempt in range(5):
            data = get_data_from_server(f'{TOP_API_URL}/family/{fid}')
            if data:
                return data
            time.sleep(0.05)
        return None

    def get_person(pid):
        for attempt in range(5):
            data = get_data_from_server(f'{TOP_API_URL}/person/{pid}')
            if data:
                return Person(data)
            time.sleep(0.05)
        return None

    def search(fid):
        if fid is None:
            return

        with lock:
            if fid in visited_families:
                return
            visited_families.add(fid)

        family_data = get_family(fid)

        if not family_data:
            return

        family = Family(family_data)

        with lock:
            if not tree.does_family_exist(fid):
                tree.add_family(family)

        person_ids = [
            family.get_husband(),
            family.get_wife()
        ] + family.get_children()

        person_ids = list(dict.fromkeys(
            pid for pid in person_ids if pid is not None
        ))

        with lock:
            new_person_ids = [
                pid for pid in person_ids
                if pid not in visited_people
            ]
            visited_people.update(new_person_ids)

        with ThreadPoolExecutor(max_workers=5) as executor:
            people = list(executor.map(get_person, new_person_ids))

        parent_families = []

        for person in people:
            if person is None:
                continue

            with lock:
                if not tree.does_person_exist(person.get_id()):
                    tree.add_person(person)

            if person.get_id() in (
                family.get_husband(),
                family.get_wife()
            ):
                parent_id = person.get_parentid()

                if parent_id is not None:
                    parent_families.append(parent_id)

        threads = []

        for parent_id in set(parent_families):
            thread = threading.Thread(
                target=search,
                args=(parent_id,)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    search(family_id)


# -----------------------------------------------------------------------------
def breadth_fs_pedigree(family_id, tree):
    # Breadth First Search using a queue and concurrent requests.
    # No recursion is used.

    visited_families = {family_id}
    visited_people = set()

    def get_family(fid):
        for attempt in range(5):
            data = get_data_from_server(f'{TOP_API_URL}/family/{fid}')
            if data:
                return data
            time.sleep(0.05)
        return None

    def get_person(pid):
        for attempt in range(5):
            data = get_data_from_server(f'{TOP_API_URL}/person/{pid}')
            if data:
                return Person(data)
            time.sleep(0.05)
        return None

    current_level = queue.Queue()
    current_level.put(family_id)

    with ThreadPoolExecutor(max_workers=100) as executor:

        while not current_level.empty():

            family_ids = []

            while not current_level.empty():
                family_ids.append(current_level.get())

            family_results = list(
                executor.map(get_family, family_ids)
            )

            families = []

            for data in family_results:
                if data:
                    family = Family(data)
                    families.append(family)

                    if not tree.does_family_exist(family.get_id()):
                        tree.add_family(family)

            person_ids = []

            for family in families:
                person_ids.extend([
                    family.get_husband(),
                    family.get_wife()
                ])
                person_ids.extend(family.get_children())

            person_ids = list(dict.fromkeys(
                pid for pid in person_ids if pid is not None
            ))

            new_person_ids = [
                pid for pid in person_ids
                if pid not in visited_people
            ]

            visited_people.update(new_person_ids)

            people = list(
                executor.map(get_person, new_person_ids)
            )

            for person in people:
                if person is not None:
                    if not tree.does_person_exist(person.get_id()):
                        tree.add_person(person)

            next_level = []

            for family in families:
                for person_id in (
                    family.get_husband(),
                    family.get_wife()
                ):
                    if person_id is None:
                        continue

                    person = tree.get_person(person_id)

                    if person is not None:
                        parent_id = person.get_parentid()

                        if (
                            parent_id is not None
                            and parent_id not in visited_families
                        ):
                            visited_families.add(parent_id)
                            next_level.append(parent_id)

            for parent_id in next_level:
                current_level.put(parent_id)


# -----------------------------------------------------------------------------
def breadth_fs_pedigree_limit5(family_id, tree):
    # Breadth First Search with a maximum of 5 worker threads.
    # No recursion is used.

    visited_families = {family_id}
    visited_people = set()

    def get_family(fid):
        for attempt in range(5):
            data = get_data_from_server(f'{TOP_API_URL}/family/{fid}')
            if data:
                return data
            time.sleep(0.05)
        return None

    def get_person(pid):
        for attempt in range(5):
            data = get_data_from_server(f'{TOP_API_URL}/person/{pid}')
            if data:
                return Person(data)
            time.sleep(0.05)
        return None

    current_level = queue.Queue()
    current_level.put(family_id)

    with ThreadPoolExecutor(max_workers=5) as executor:

        while not current_level.empty():

            family_ids = []

            while not current_level.empty():
                family_ids.append(current_level.get())

            family_results = list(
                executor.map(get_family, family_ids)
            )

            families = []

            for data in family_results:
                if data:
                    family = Family(data)
                    families.append(family)

                    if not tree.does_family_exist(family.get_id()):
                        tree.add_family(family)

            person_ids = []

            for family in families:
                person_ids.extend([
                    family.get_husband(),
                    family.get_wife()
                ])
                person_ids.extend(family.get_children())

            person_ids = list(dict.fromkeys(
                pid for pid in person_ids if pid is not None
            ))

            new_person_ids = [
                pid for pid in person_ids
                if pid not in visited_people
            ]

            visited_people.update(new_person_ids)

            people = list(
                executor.map(get_person, new_person_ids)
            )

            for person in people:
                if person is not None:
                    if not tree.does_person_exist(person.get_id()):
                        tree.add_person(person)

            next_level = []

            for family in families:
                for person_id in (
                    family.get_husband(),
                    family.get_wife()
                ):
                    if person_id is None:
                        continue

                    person = tree.get_person(person_id)

                    if person is not None:
                        parent_id = person.get_parentid()

                        if (
                            parent_id is not None
                            and parent_id not in visited_families
                        ):
                            visited_families.add(parent_id)
                            next_level.append(parent_id)

            for parent_id in next_level:
                current_level.put(parent_id)
