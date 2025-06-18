class InvalidKeyError(ValueError):
    def __init__(self, key: str) -> None:
        msg = f"Invalid key: {key}"
        super().__init__(msg)
