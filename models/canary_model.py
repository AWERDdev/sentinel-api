from pydantic import BaseModel , Field
from datetime import datetime
from typing import Optional

class CanaryToken(BaseModel):
    token_ID: str = Field(..., description="This is the unique ID for the token")
    token_type: str = Field(..., description="This decides what kind of token it is")
    name: str = Field(..., description="This is an easy way to find specific tokens")
    alert_email: str = Field(..., description="where to send the alert message if triggered")
    created_at: datetime = Field(..., description="The date when the token is made")
    is_active: bool = Field(default=True)
    auth_string: Optional[str] = Field(None, description="The actual fake password/key/URL given to the user")
