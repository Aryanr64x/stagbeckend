from pydantic import BaseModel

class TextToTextEmbedRequest(BaseModel):
    secret: str
    cover: str
    
    
    
class TextToTextRecoverRequest(BaseModel):
    embedded: str


