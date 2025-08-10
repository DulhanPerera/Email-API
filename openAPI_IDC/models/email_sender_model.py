from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any, ForwardRef
from datetime import date

# Forward references for type hints
EmailBodyModel = ForwardRef('EmailBodyModel')
TableFilterInfo = ForwardRef('TableFilterInfo')

class TableFilterInfo(BaseModel):
    Name: str
    CompanyName: str
    BillingCenter: str
    Arrears: float

class EmailBodyModel(BaseModel):
    Sender_Name: str
    Table_Filter_infor: Optional[TableFilterInfo]

class EmailSenderRequest(BaseModel):
    Type: str
    SendersMail: EmailStr
    CarbonCopyTo: List[EmailStr]
    Subject: str
    TemplateName: str
    EmailBody: EmailBodyModel
    Attachments: List[str] = []
    Date: date

# Resolve forward references
EmailBodyModel.update_forward_refs()
TableFilterInfo.update_forward_refs()

