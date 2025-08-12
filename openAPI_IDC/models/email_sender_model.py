from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any, ForwardRef, Dict
from datetime import date

# Forward references for type hints
EmailBodyModel = ForwardRef('EmailBodyModel')
TableFilterInfo = ForwardRef('TableFilterInfo')

class TableFilterInfo(BaseModel):
    # This will store all the dynamic fields
    data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = 'allow'  # This allows extra fields
    
    def __init__(self, **data):
        # Store all fields in the data dictionary
        super().__init__(**{'data': {**data}})
        self.data.update(data)

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

