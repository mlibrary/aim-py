import typer
from aim.hathifiles import poll
from aim.services import S

app = typer.Typer()


@app.command()
def create_store_file():
    f"""
    Genereates a new store file at {S.hathifiles_store_path} if one does not
    already exist. The new file is based on the latest hathi_files_list.json
    from hathitrust.org 
    """
    poll.create_store_file()


@app.command()
def check_for_new_update_files():
    """
    Pulls the latest hathi_files_list.json from hathitrust.org and checks if
    there are any update files that aren't in the store. If there are new files
    it notifies the argo events webhook and replaces the store file with the old
    files and the new ones.
    """
    poll.check_for_new_update_files()
