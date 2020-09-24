import bz2
import os
import sqlite3
import pandas as pd

class Importer():
    path = './db/'
    db_name = 'eve.db'
    output_filename = 'eve.db.bz2file'
    url = 'https://www.fuzzwork.co.uk/dump/sqlite-latest.sqlite.bz2'

    def __init__(self):
        self.db = os.path.abspath(EVEDB_PATH)
        self.conn = sqlite3.connect(db)

    def cache_tables(self):
        types_q = """select  * from  invTypes """
        activities_q = """select * from industryActivity"""
        products_q = """select * from industryActivityProducts"""
        materials_q = """select * from industryActivityMaterials"""
        self.tables = {
            "types": pd.read_sql_query(types_q, self.conn),
            "activity": pd.read_sql_query(activities_q, self.conn),
            "products": pd.read_sql_query(products_q, self.onn),
            "materials": pd.read_sql_query(materials_q, self.conn),
        }

    def download_db():
        res = requests.get(url, stream=True)
        output = "%s/%s" % (path, output_filename)
        if res.status_code != 200:
            print("Cannot download the file.")
            print(res.content)
        try:
            total_size = 0
            with open(output, "wb") as handle:
                for data in res.iter_content(1024 * 1024 * 10):
                    print(
                        "\rDownloading file ... [%s]             " % (
                            get_human_size(total_size)
                        ),
                        end=""
                    )
                    handle.write(data)
                    total_size += len(data)

        except Exception as err:
            print("\rDownloading file ... [FAILED]             ")
            print(str(err))
            return False

        print("\rDownloading file ... [SUCCESS]             ")
        return True 

    def bunzip2(self, path, source_filename, dest_filename):
        source_file = "%s/%s" % (path, source_filename)
        try:
            print("Decompressing file ... ", end='')
            with open(source_file, 'rb') as bz2file:
                with open(dest_filename, 'wb') as unzipped_file:
                    decompressor = bz2.BZ2Decompressor()
                    for data in iter(lambda: bz2file.read(100 * 1024), b''):
                        unzipped_file.write(decompressor.decompress(data)) 
