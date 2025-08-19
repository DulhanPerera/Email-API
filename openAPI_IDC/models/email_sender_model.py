from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any, ForwardRef, Dict
from datetime import date

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
    Reciever_Name: str
    Table_Filter_infor: Optional[TableFilterInfo]

class EmailSenderRequest(BaseModel):
    EmailType: str
    RecieverMail: EmailStr
    CarbonCopyTo: List[EmailStr]
    Subject: str
    EmailBody: EmailBodyModel
    Attachments: List[str] = []

