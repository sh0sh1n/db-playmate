from db_playmate.box import get_client
import toml
from db_playmate.databrary import Databrary
from db_playmate.kobo import Kobo
import os
import shutil
import db_playmate.constants as constants
from db_playmate.configure import get_creds

"""
This is the bridge between Box and Kobo/Databrary.
Used to transfer files between the three systems.
This class also will hold instances of all three connections
"""


class Bridge:
    def __init__(self, config_file):

        try:
            with open(config_file) as config:
                cfg = toml.load(config)
                clid = cfg["box"]["client_id"]
                databrary_username = cfg["databrary"]["username"]
                kobo_base_url = cfg["kobo"]["base_url"]
        except:
            pass  # It is OK if the creds are already in place and we called twice

        kobo_token, clsec = get_creds()

        print("Connecting to Box...")
        self.box = get_client(clid, clsec)
        print("Connecting to Kobo...")
        self.kobo = Kobo(kobo_base_url, kobo_token)
        print("Connecting to Databrary...")
        self.db = Databrary(databrary_username)

    def transfer_box_to_databrary(
        self, box_path, db_volume, db_container, rename_file=None
    ):
        """
        Rename file is optional, if so specify the filename to use on databrary)
        """
        # First, get the file from box
        # This returns a box file object, not the download
        box_file = self.box.get_file(box_path)

        # Now open an output stream into databrary
        # TODO

    def transfer_file_to_box(self, filename, box_path, makedirs=False):
        self.box.upload_file(filename, box_path, makedirs=makedirs)

    def transfer_databrary_to_box(self, db_asset, box_path):
        """
        Transfer a file from databrary to Box
        """
        # TODO expose the file name changing part of the download function
        file_stream, total_size, filename = self.db.download_asset_stream(db_asset)
        total_size_mb = total_size / 1000 / 1000
        download_dir = constants.TMP_DATA_DIR
        if total_size_mb < 200:  # KB
            try:
                os.mkdir(download_dir)
            except:
                pass
            f = self.db.download_asset(db_asset, download_dir)
            self.box.upload_file(f, box_path, db_asset.play_filename)

            try:
                shutil.rmtree(download_dir)
            except:
                pass
        else:
            self.box.upload_file_stream(
                file_stream, box_path, total_size, db_asset.play_filename
            )

    def transfer_kobo_to_box(self):
        try:
            self.box.delete("kobo")
        except Exception as e:
            print(e)
        try:
            self.box.create_folder("", "kobo")
        except Exception as e:
            print(e)
        forms = self.kobo.get_forms()
        for form in forms.values():
            print(f"{form.name}: {form.num_submissions} submissions. Downloading...")
            filename = constants.TMP_DATA_DIR + "/" + form.name + ".csv"
            with open(filename, "w+") as outfile:
                form.to_csv(outfile)
            print("Uploading to Box...")
            self.box.upload_file(filename, "kobo")
            print("Deleting kobo file...")
            os.remove(filename)
