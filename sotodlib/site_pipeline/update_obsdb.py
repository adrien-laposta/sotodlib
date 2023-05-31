"""update_obsdb
The config file could be of the form:
.. code-block:: yaml

    obsdb: dummydb.yaml
    cols:
        start_time: float
        end_time: float
        n_samples: int
        telescope: str
        tube_slot: str
        type: str

"""
from sotodlib.core.metadata import ObsDb
from sotodlib.core import Context 
from sotodlib.site_pipeline.check_book import main as checkbook
import os
import glob
import yaml
import numpy as np
import time
import argparse


def check_meta_type(bookpath):
    metapath = os.path.join(bookpath, "M_index.yaml")
    meta = yaml.safe_load(open(metapath, "rb"))
    if meta is None:
        return "empty"
    elif "type" not in meta:
        return "notype"
    else:
        return meta["type"]

def update_obsdb(base_dir, 
                 config="config.yaml", 
                 recency=2., 
                 verbosity=2, 
                 booktype="both"):
    """
        Create or update an obsdb for observation or operations data.
    Argument
    ----------
    base_dir : str
        The base directory in which to look for books
    Parameters
    ----------
    config : str
        Path to config file
    recency : float
        How far back in time to look for databases, in days. (default: 2.)
    booktype : str
        Look for observations or operations data or both (default: both)
    """
    bookcart = []
    bookcartobsdb = ObsDb()

    if booktype=="both":
        accept_type = ["obs", "oper"]
    else:
        accept_type = [booktype]

    configs = yaml.safe_load(open(config, "r"))
    if "obsdb" in configs:
        if os.path.isfile(configs["obsdb"]):
            bookcartobsdb = ObsDb.from_file(configs["obsdb"])
    if "cols" in configs:
        col_list = []
        for col, typ in configs["cols"].items():
            col_list.append(col+" "+typ)
        bookcartobsdb.add_obs_columns(col_list)

    #How far back we should look
    tnow = time.time()
    tback = tnow - recency*86400
    #Find folders that are book-like and recent
    for dirpath,_, _ in os.walk(base_dir):
        last_mod = max(os.path.getmtime(root) for root,_,_ in os.walk(dirpath))
        if last_mod<tback:#Ignore older directories
            continue
        if os.path.exists(os.path.join(dirpath, "M_index.yaml")):
            #Looks like a context file
            bookcart.append(dirpath)
    #Check the books for the observations we want

    for bookpath in bookcart:
        if check_meta_type(bookpath) in accept_type:
            """ obsfiledb creation
            The extra files give us a bit of trouble. We'll assume that index,
            book, and bookbinder_log are always here, and edit our config file
            to cover the rest as extra files.
            """
            book_file_list = os.listdir(bookpath)
            book_file_list.remove("M_index.yaml")
            book_file_list.remove("M_book.yaml")
            book_file_list.remove("Z_bookbinder_log.txt")
            book_file_list = [file_name for file_name in book_file_list if not file_name.endswith(".g3")]
            if len(book_file_list)>0:
                configs["extra_extra_files"] += book_file_list
                with open(config, "w") as config_file:
                    yaml.dump(configs, config_file)
                checkbook(bookpath, config, add=True)
                configs["extra_extra_files"] = ["Z_bookbinder_log.txt"]
                with open(config, "w") as config_file:
                    yaml.dump(configs, config_file)

            else:
                checkbook(bookpath, config, add=True)

            index = yaml.safe_load(open(os.path.join(bookpath, "M_index.yaml"), "rb"))
            obs_id = index.pop("book_id")
            tags = index.pop("tags")
            detsets = index.pop("detsets")

            if "cols" in configs:
                very_clean = {col:index[col] for col in iter(configs["cols"]) if col in index}
            else:
                col_list = []
                clean = {key:val for key, val in index.items() if val is not None}
                very_clean = {key:val for key, val in clean.items() if type(val) is not list}
                for key, val in very_clean.items():
                    col_list.append(key+" "+type(val).__name__)
                bookcartobsdb.add_obs_columns(col_list)

            if tags != ([] or [""]):
                bookcartobsdb.update_obs(obs_id, very_clean, tags=tags)
            else:
                bookcartobsdb.update_obs(obs_id, very_clean)
           
        else:
            bookcart.remove(bookpath)
    if "obsdb" in configs:
        bookcartobsdb.to_file(configs["obsdb"])
    else:
        bookcartobsdb.to_file("obsdb_from{}_to{}".format(tback, tnow))


def get_parser(parser=None):
    if parser is None:
        parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, 
        help="base directory from which to look for books")
    parser.add_argument("--config", help="ObsDb configuration file",
        default="config.yaml", type=str)
    parser.add_argument('--recency', default=2, type=float,
        help="Days to subtract from now to set as minimum ctime")
    parser.add_argument("--verbosity", default=2, type=int,
        help="Increase output verbosity. 0:Error, 1:Warning, 2:Info(default), 3:Debug")
    parser.add_argument("--booktype", default="both", type=str,
        help="Select book type to look for: obs, oper, both(default)")
    return parser
def main():
    parser = get_parser(parser=None)
    args = parser.parse_args()
    update_obsdb(**vars(args))


if __name__ == '__main__':
    main()
