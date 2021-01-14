import requests
from pathlib import Path

import bz2
import sqlite3
import pandas as pd

from fetchlib.utils import CLASSES_GROUPS, PATH

DB_NAME = "eve.db"
OUTPUT_FILENAME = "eve.db.bz2file"
URL = "https://www.fuzzwork.co.uk/dump/sqlite-latest.sqlite.bz2"


class ImporterSingleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance or not (PATH / DB_NAME).exists():
            cls._instance = super(ImporterSingleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instance


class Importer(metaclass=ImporterSingleton):

    # Singleton class
    def __init__(self):

        self.db = PATH / DB_NAME
        if not (PATH / DB_NAME).exists():
            self.__download_db()
            self.__bunzip2()
        self.conn = sqlite3.connect(str(self.db))
        self.__cache_tables()

    def __get_group_content_names(self, group_id):
        return pd.read_sql_query(
            "select * from invTypes where marketGroupID == {} ".format(
                group_id
            ),
            self.conn,
        )["typeName"]

    def __get_class_contents(self, classname):
        ids = CLASSES_GROUPS[classname]
        res = []
        for i in ids:
            res.extend(list(self.__get_group_content_names(i)))
        return res

    def __cache_tables(self):
        types_q = """select  * from  invTypes """
        activities_q = """select * from industryActivity"""
        products_q = """select * from industryActivityProducts"""
        materials_q = """select * from industryActivityMaterials"""
        marketgroups_q = """select * from invMarketGroups"""

        # Remove 'test reaction' from tables
        activity = pd.read_sql_query(activities_q, self.conn)
        activity = activity[activity["typeID"] != 45732]
        products = pd.read_sql_query(products_q, self.conn)
        products = products[products["typeID"] != 45732]

        self.tables = {
            "types": pd.read_sql_query(types_q, self.conn),
            "activity": activity,
            "products": products,
            "materials": pd.read_sql_query(materials_q, self.conn),
            "marketgroups": pd.read_sql_query(marketgroups_q, self.conn),
        }
        self.component_by_classes = {
            key: self.__get_class_contents(key)
            for key in CLASSES_GROUPS.keys()
        }

    def __download_db(self):
        res = requests.get(URL, stream=True)
        PATH.mkdir(parents=True, exist_ok=True)
        output = PATH / OUTPUT_FILENAME
        if res.status_code != 200:
            print("Cannot download the file.")
            print(res.content)
        try:
            total_size = 0
            with open(output, "wb") as handle:
                for data in res.iter_content(1024 * 1024 * 10):
                    print(
                        "\rDownloading file ... [%s]             "
                        % (get_human_size(total_size)),
                        end="Path: {}".format(output),
                    )
                    handle.write(data)
                    total_size += len(data)

        except Exception as err:
            print("\rDownloading file ... [FAILED]             ")
            print(str(err))
            return False
        print("\rDownloading file: {}  [SUCCESS]             ".format(output))
        return True

    def __bunzip2(self):
        source_file = Path(PATH, OUTPUT_FILENAME)
        dest_file = self.db
        try:
            print("Decompressing file ... ", end="")
            with open(source_file, "rb") as bz2file:
                with open(dest_file, "wb") as unzipped_file:
                    decompressor = bz2.BZ2Decompressor()
                    for data in iter(lambda: bz2file.read(100 * 1024), b""):
                        unzipped_file.write(decompressor.decompress(data))
        except Exception as e:
            print(str(e))

        print(
            "Succesfully finished decompression: source: {},  dest: {}".format(
                source_file, dest_file
            )
        )


def get_human_size(size, precision=2):
    """ Display size in human readable str """
    suffixes = ["B", "KB", "MB", "GB", "TB"]
    suffixIndex = 0
    while size > 1024 and suffixIndex < 4:
        suffixIndex += 1  # increment the index of the suffix
        size = size / 1024.0  # apply the division
    return "%.*f%s" % (precision, size, suffixes[suffixIndex])
