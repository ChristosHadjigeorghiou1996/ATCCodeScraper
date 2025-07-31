from dataclasses import dataclass

@dataclass
class ATCCode:
    """
    Dataclass of ATC code
    """
    code: str
    name: str
    url: str
