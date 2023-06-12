import bz2
import sqlite3
from abc import ABC, abstractproperty
from pathlib import Path

import pandas as pd
import requests

from fetchlib.utils import CLASSES_GROUPS, PATH


DB_NAME = "eve.db"
OUTPUT_FILENAME = "eve.db.bz2file"
URL = "https://www.fuzzwork.co.uk/dump/sqlite-latest.sqlite.bz2"


class AbstractDataExport(ABC):
    @abstractproperty
    def products(self):
        raise NotImplementedError

    @abstractproperty
    def materials(self):
        raise NotImplementedError

    @abstractproperty
    def types(self):
        raise NotImplementedError

    @abstractproperty
    def activities(self):
        raise NotImplementedError

    @abstractproperty
    def market_gropups(self):
        raise NotImplementedError

    def enrich_collection(self, collection: pd.DataFrame) -> pd.DataFrame:
        result = collection.merge(
            self.types,
            left_on="productName",
            right_on="typeName",
        )[["typeName", "typeID", "run", "me_impact", "te_impact"]]
        return result

    def append_products(self, step: pd.DataFrame) -> pd.DataFrame:
        result = step.set_index("typeID").join(
            self.productables.set_index("productTypeID"),
            rsuffix="_product",
            how="inner",
        )
        return result

    @property
    def filtrated_materials(self) -> pd.DataFrame:
        # Remove everything but 'reaction' and 'production'
        materials = self.materials
        result = materials[materials["activityID"].isin([1, 11])]
        return result

    @property
    def productables(self) -> pd.DataFrame:
        products = self.products
        # Keep only reaction and production
        products = products[products["activityID"].isin((1, 11))]
        return products

    def append_materials(self, table: pd.DataFrame) -> pd.DataFrame:
        filtrated = self.filtrated_materials.set_index("typeID")
        result = table.set_index("typeID").join(
            filtrated, how="inner", rsuffix="_materials"
        )
        return result

    def append_prices(self, step: pd.DataFrame) -> pd.DataFrame:
        types = self.types.set_index("typeID")
        result = step.set_index("materialTypeID").join(
            types, how="inner", rsuffix="_prices"
        )
        return result

    def append_everything(self, step: pd.DataFrame) -> pd.DataFrame:
        with_products = self.append_products(step)
        with_materials = self.append_materials(with_products)
        with_prices = self.append_prices(with_materials)
        return with_prices

    def pretify_step(self, table: pd.DataFrame):
        """
        Helper for fancyfing step
        """
        step = self.append_products(table)[
            ["typeID", "quantity", "activityID"]
        ]

        # Reseting typeID to coresponds item, not item's blueprint
        step["typeID"] = step.index

        types = self.types.set_index("typeID")
        step = self.append_products(step).join(types)
        step["runs_required"] = step["quantity"] / step["quantity_product"]

        # Reseting typeID to coresponds item, not item's blueprint
        step["typeID"] = step.index

        return step[
            ["typeName", "quantity", "runs_required", "activityID", "typeID"]
        ]

    def atomic_materials(self, atomic: pd.DataFrame) -> pd.DataFrame:
        """
        Helper for fancyfing atomic
        """
        types = self.types
        materials = (
            atomic[["typeID", "quantity"]]
            .astype({"typeID": "int64"})
            .groupby("typeID")
            .sum()
        )
        materials = materials.join(
            types.set_index("typeID"), lsuffix="-atom_"
        )[["typeName", "quantity"]].astype({"quantity": "int64"})
        return materials.reset_index()

    def create_init_table(self, **kwargs) -> pd.DataFrame:
        """
        Method to create initial Pandas dataframe

        params:
        kwargs: Dict[str, int] - dictionary of items to produce with corresponding quantities
        """
        init = pd.DataFrame(
            kwargs.items(), columns=["typeName", "quantity"]
        ).set_index("typeName")
        types = self.types.set_index("typeName")
        with_types = init.join(types)[["typeID", "quantity"]]
        if diff := set(kwargs.keys()) - set(with_types.index):
            raise ValueError(f"No such products in database: {diff}")
        prety = self.pretify_step(with_types)
        return prety


class StaticDataExport(AbstractDataExport):
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
        activities = pd.read_sql_query(activities_q, self.conn)
        products = pd.read_sql_query(products_q, self.conn)

        self._tables = {
            "types": pd.read_sql_query(types_q, self.conn),
            "activities": activities,
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

    @property
    def activities(self):
        table = self._tables["activities"]

        # SDE contains 'testing' reaction with id = 45732
        # This one not represented in-game and breaks decomposition algo

        table = table[table["typeID"] != 45732]

        return table

    @property
    def products(self):
        table = self._tables["products"]

        # SDE contains 'testing' reaction with id 45732
        # This one not represented in-game and breaks decomposition algo

        table = table[table["typeID"] != 45732]
        return table

    @property
    def types(self):
        return self._tables["types"]

    @property
    def materials(self):
        return self._tables["materials"]

    @property
    def market_gropups(self):
        return self._tables["marketgroups"]


def get_human_size(size, precision=2):
    """Display size in human readable str"""
    suffixes = ["B", "KB", "MB", "GB", "TB"]
    suffixIndex = 0
    while size > 1024 and suffixIndex < 4:
        suffixIndex += 1  # increment the index of the suffix
        size = size / 1024.0  # apply the division
    return "%.*f%s" % (precision, size, suffixes[suffixIndex])
