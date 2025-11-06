from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy import text, Connection
from aim.services import S
from pydantic import BaseModel, Field
from datetime import datetime


class Item(BaseModel):
    """
    A Hahtilfiles Item. All of the documentation comes from https://www.hathitrust.org/member-libraries/resources-for-librarians/data-resources/hathifiles/hathifiles-description/
    """

    htid: str = Field(..., description="HathiTrust Id")
    access: bool = Field(..., description="Whether or not users can view the item.")
    rights_code: str = Field(
        ...,
        description="A code (also referred to as “rights attribute”) that describes the copyright status, license or access. See the full list of codes: https://www.hathitrust.org/the-collection/preservation/rights-database/#attributes ",
    )
    bib_num: int = Field(
        ...,
        description="HathiTrust's record number for the associated bibliographic record. HathiTrust record numbers are not permanent and can change over time. URLs to HathiTrust catalog records can be constructed as follows: https://catalog.hathitrust.org/Record/record_number For example: https://catalog.hathitrust.org/Record/001285647",
    )
    description: str = Field(
        "",
        description='Enumeration (e.g., "vol.1") and chronology (e.g., "1883", "Jun-Oct 1927") data for this item. ',
    )
    source: str = Field(
        "",
        description="Code identifying the source of the bibliographic record. Currently, the NUC code of the originating library is used for the code.",
    )
    source_bib_num: str = Field(
        ...,
        description="Local bibliographic record number used in the catalog of the library that contributed the item. ",
    )
    oclc: list[str] = Field(
        [], description="OCLC number(s) for the bibliographic record."
    )
    isbn: list[str] = Field([], description="ISBN(s) for the bibliographic record.")
    issn: list[str] = Field([], description="ISSN(s) for the bibliographic record.")
    lccn: list[str] = Field([], description="LCCN(s) for the bibliographic record.")
    title: str = Field(
        "",
        description="The title of the work. May include an author if provided in the MARC field 245 $c. Includes all subfields of the 245 MARC field.",
    )
    imprint: str = Field(
        "",
        description="The name of the publisher and the date of publication. Includes subfieds b and c of the 260 MARC field.",
    )
    rights_reason: str = Field(
        "",
        description="This code describes how the “Rights” code was set. See the full list of Reason Codes.",
    )
    rights_timestamp: datetime = Field(
        ...,
        description="This date may change when any of the following activities occur: the item was newly deposited into the collection a new copy of the digital item overrode the previous copy the rights and access status has changed a new bibliographic record was provided by the contributor",
    )
    us_gov_doc_flag: bool = Field(
        ..., description="United States federal government document indicator."
    )
    rights_date_used: int = Field(
        ...,
        description="Derived publication date of the item. The date is derived from data provided in the 008 field of the MARC record and the enumeration/chronology data for the item. In cases where the date of the item could not be easily determined by HathiTrust processes, the date will be listed in the hathifiles as 9999. ",
    )
    pub_place: str = Field(
        "",
        description="The place of publication for the work. The codes included in this data element were originally provided in bytes 15-17 of the 008 MARC field. See the full list of country codes in the “MARC Code List for Countries.”",
    )
    lang_code: str = Field(
        "",
        description="The primary language of the work. The codes included in this data element were originally provided in bytes 35-37 of the 008 MARC field. See the full list of language codes in the “MARC code list for Languages.” ",
    )
    bib_fmt: str = Field(
        "",
        description="Bibliographic format of the work. Definitions of format values can be found on the Library of Congress website Permitted values include: BK - monographic book SE - serial, continuing resources (e.g., journals, newspapers, periodicals) CF - computer files and electronic resources MP - maps, including atlases and sheet maps MU - music, including sheet music VM - visual material MX - mixed materials",
    )
    collection_code: str = Field(
        "",
        description="An administrative code used to share information between Zephir and HathiTrust repository.*",
    )
    content_provider_code: str = Field(
        "",
        description="The institution that originally contributed the content. Codes used are listed at https://www.hathitrust.org/institution_identifiers.*",
    )
    responsible_entity_code: str = Field(
        "",
        description="The institution that took responsibility for accessioning the content into HathiTrust, in cases where the content provider was not a member of HathiTrust. Codes used are listed at https://www.hathitrust.org/institution_identifiers.*",
    )
    digitization_agent_code: str = Field(
        "",
        description="The organization that digitized the content. Codes used are listed at https://www.hathitrust.org/rights_database#Sources.*",
    )
    access_profile_code: str = Field(
        "",
        description="Access profiles indicate whether an item has view or download restrictions. They work in combination with the rights codes (included in the hathifiles in data element “rights”) to determine user access. Permitted values include: open - Items with this value do not have any download restrictions. google - Items with this value have some download restrictions. Any user anywhere can download one page at a time. Member-affiliated users can download the full pdf. page - Items with this value can be viewed on the HathiTrust website. Users can download individual pages but cannot download the full pdf, regardless of member affiliation. page+lowres - Users can download the item in a lower resolution with a watermark only.",
    )
    author: str = Field(
        "",
        description="The name of the person, company or meeting that created the work. Author names are typically in authorized format, meaning that the name is provided in a standardized form used across multiple catalogs and databases. Includes the following fields from the MARC record: 100 $a $b $c $d - Name of the person who authored the work 110 $a $b $c $d - Name of a corporation or organization that authored the work 111 $a $c $d - Name of a meeting or conference that is responsible for creating the work",
    )


engine = create_engine(S.hathifiles_mysql_database, pool_pre_ping=True)

description = """
The Hathifiles Database API enables getting information about items in HathiTrust 
"""
app = FastAPI(title="Hathifiles", description=description)


# Dependency
def get_db():  # pragma: no cover
    db = engine.connect()
    try:
        yield db
    finally:
        db.close()


@app.get("/items/{htid}", response_model_exclude_defaults=True)
# def get_item(htid: str, db: Connection = Depends(get_db)):
def get_item(htid: str, db: Connection = Depends(get_db)) -> Item:
    """
    Get a Hathifiles Item by HathiTrust id
    """
    query = text(f"SELECT * FROM hf WHERE htid='{htid}'")
    result = db.execute(query)
    item = result.first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    return ItemModel(item)


class ItemModel:
    def __init__(self, data):
        self._data = data
        self.htid = self._data.htid
        self.access = self._data.access
        self.rights_code = self._data.rights_code
        self.bib_num = self._data.bib_num
        self.description = self._data.description
        self.source = self._data.source
        self.source_bib_num = self._data.source_bib_num
        self.title = self._data.title
        self.imprint = self._data.imprint
        self.rights_reason = self._data.rights_reason
        self.rights_timestamp = self._data.rights_timestamp
        self.us_gov_doc_flag = self._data.us_gov_doc_flag
        self.rights_date_used = self._data.rights_date_used
        self.pub_place = self._data.pub_place
        self.lang_code = self._data.lang_code
        self.bib_fmt = self._data.bib_fmt
        self.collection_code = self._data.collection_code
        self.content_provider_code = self._data.content_provider_code
        self.responsible_entity_code = self._data.responsible_entity_code
        self.digitization_agent_code = self._data.digitization_agent_code
        self.access_profile_code = self._data.access_profile_code
        self.author = self._data.author

    @property
    def oclc(self):
        return self._get_list(self._data.oclc)

    @property
    def isbn(self):
        return self._get_list(self._data.isbn)

    @property
    def issn(self):
        return self._get_list(self._data.issn)

    @property
    def lccn(self):
        return self._get_list(self._data.lccn)

    def _get_list(self, string_list):
        return filter(None, string_list.split(","))
