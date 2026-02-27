class DomainError(Exception):
    pass

class NotFound(DomainError):
    pass

class InvalidStatusTransition(DomainError):
    def __init__(self, current: str, new: str):
        super().__init__(f"Invalid status transition: {current} -> {new}")
