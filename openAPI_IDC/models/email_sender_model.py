from pydantic import BaseModel
from typing import List, Optional,Any
from pydantic import BaseModel
from datetime import datetime


class EmailSenderRequest(BaseModel):
    Type: str
    SendersMail: EmailStr
    CarbonCopyTo: List[EmailStr]
    Subject: str
    TemplateName: str
    EmailBody: EmailBodyModel
    Attachments: List[str]
    Date: date

class EmailBodyModel(BaseModel):
    Sender_Name: str
    Table_Filter_infor: Optional[TableFilterInfo]

class TableFilterInfo(BaseModel):
    Name: str
    CompanyName: str
    BillingCenter: str
    Arrears: float

