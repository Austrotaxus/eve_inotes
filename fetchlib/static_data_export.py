import bz2
import sqlite3
from abc import ABC, abstractproperty
from functools import cache
from pathlib import Path
from typing import List

import pandas as pd
import requests

from fetchlib.utils import CLASSES_GROUPS, PATH, ProductionClass

DB_NAME = "eve.db"
OUTPUT_FILENAME = "eve.db.bz2file"
URL = "https://www.fuzzwork.co.uk/dump/sqlite-latest.sqlite.bz2"


class AbstractDataExport(ABC):
    """DataExport is defined by 5 pandas tables tables(abstractproperty).
    Instance is used in during Decompositor application and Setup creation.
    """

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
    def market_groups(self):
        raise NotImplementedError

    def append_type_id(self, collection: pd.DataFrame) -> pd.DataFrame:
        """
        Args:
            collection - pandas DataFrame indexed by 'typeName'.
        Returns:
            Dataframe with 'typeName' and 'typeID' columns.
        """
        result = collection.join(
            self.types.set_index("typeName"),
        )[["typeID", "run", "me_impact", "te_impact"]]
        return result.reset_index(names="typeName")

    def append_products(self, step: pd.DataFrame) -> pd.DataFrame:
        result = step.set_index("typeID").join(
            self.products.set_index("productTypeID"),
            rsuffix="_product",
            how="inner",
        )
        return result

    def append_materials(self, table: pd.DataFrame) -> pd.DataFrame:
        filtrated = self.materials.set_index("typeID")
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
        """Helper for fancyfing step."""

        step = self.append_products(table)[["typeID", "quantity", "activityID"]]

        # Reseting typeID to coresponds item, not item's blueprint

        step["typeID"] = step.index

        types = self.types.set_index("typeID")
        step = self.append_products(step).join(types)
        step["runs_required"] = step["quantity"] / step["quantity_product"]

        # Reseting typeID to coresponds item, not item's blueprint

        step["typeID"] = step.index

        return step[["typeName", "quantity", "runs_required", "activityID", "typeID"]]

    def atomic_materials(self, atomic: pd.DataFrame) -> pd.DataFrame:
        """Helper for fancyfing atomic."""
        types = self.types
        materials = (
            atomic[["typeID", "quantity"]]
            .astype({"typeID": "int64"})
            .groupby("typeID")
            .sum()
        )
        materials = materials.join(types.set_index("typeID"), lsuffix="-atom_")[
            ["typeName", "quantity"]
        ].astype({"quantity": "int64"})
        return materials.reset_index()

    def create_init_table(self, **kwargs) -> pd.DataFrame:
        """Method to create initial Pandas dataframe.

        Args:
            kwargs: Dict[str, int] - dictionary of items to produce with corresponding quantities.
        """
        init = pd.DataFrame(kwargs.items(), columns=["typeName", "quantity"]).set_index(
            "typeName"
        )
        types = self.types.set_index("typeName")
        with_types = init.join(types)[["typeID", "quantity"]]
        if diff := set(kwargs.keys()) - set(with_types.index):
            raise ValueError(f"No such products in database: {diff}")
        prety = self.pretify_step(with_types)
        return prety

    def get_class_contents(self, production_class: str) -> pd.DataFrame:
        """
        Returns:
            List of typeNames which belongs to production_class
        """
        group_ids = list(CLASSES_GROUPS[production_class].values())
        return self._get_types_by_group_ids(*group_ids)

    def _get_types_by_group_ids(self, *group_ids) -> List[str]:
        res = list(self.types[self.types["marketGroupID"].isin(group_ids)]["typeName"])
        return res


class StaticDataExport(AbstractDataExport):
    """DataExport created from eve StaticDataExport sqlite3 database.
    Used in production code
    """

    def __init__(self, db_path=PATH / DB_NAME):
        self.db_path = db_path
        if not (self.db_path).exists():
            self.__download_db()
            self.__bunzip2()
        self.conn = sqlite3.connect(str(self.db_path))

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
        dest_file = self.db_path
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
    @cache
    def activities(self):
        activities_q = """
            select
                a.typeID, activityID, time
            from
                industryActivity a join invTypes t
            on
                a.typeID = t.typeID
            where
                t.published and
                a.activityID in (1,11)
            """

        table = pd.read_sql_query(activities_q, self.conn)
        return table

    @property
    @cache
    def products(self):
        products_q = """
            select
                p.typeID as typeID, activityID, productTypeID, quantity
            from
                industryActivityProducts p join invTypes t
            on p.typeID == t.typeID
            where
                t.published and
                p.activityID in (1,11)
            """
        table = pd.read_sql_query(products_q, self.conn)
        return table

    @property
    @cache
    def types(self):
        types_q = """select  * from  invTypes """
        table = pd.read_sql_query(types_q, self.conn)
        return table

    @property
    @cache
    def materials(self):
        materials_q = """
            select *
            from
                industryActivityMaterials
            where activityID in (1,11)
            """

        table = pd.read_sql_query(materials_q, self.conn)
        return table

    @property
    @cache
    def market_groups(self):
        marketgroups_q = """select * from invMarketGroups"""
        table = pd.read_sql_query(marketgroups_q, self.conn)
        return table


def get_human_size(size, precision=2):
    """Display size in human readable str"""
    suffixes = ["B", "KB", "MB", "GB", "TB"]
    suffixIndex = 0
    while size > 1024 and suffixIndex < 4:
        suffixIndex += 1  # increment the index of the suffix
        size = size / 1024.0  # apply the division
    return "%.*f%s" % (precision, size, suffixes[suffixIndex])


sde = StaticDataExport()
