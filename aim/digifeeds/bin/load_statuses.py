from aim.digifeeds.database.models import load_statuses
from aim.digifeeds.database.main import SessionLocal
import sys

def main():
    with SessionLocal() as db_session:
      load_statuses(session=db_session)

if __name__=='__main__':
    sys.exit(main())