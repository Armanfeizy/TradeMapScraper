from .base import FilterBase

HS_CODES = ["7403", "7407", "7408", "7409", "7410", "7411", "7412", "7413"]


class Product(FilterBase):
    HS_7403 = "7403"
    HS_7407 = "7407"
    HS_7408 = "7408"
    HS_7409 = "7409"
    HS_7410 = "7410"
    HS_7411 = "7411"
    HS_7412 = "7412"
    HS_7413 = "7413"

    def get_value(self) -> str:
        return self.value
