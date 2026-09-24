class DomainError(Exception):
    """Raised when a domain rule refuses an operation. The message is shown to the user."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
