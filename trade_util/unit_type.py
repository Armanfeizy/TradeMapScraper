from trade_util.base import FilterBase


class UnitType(FilterBase):
    US_DOLLAR = 1
    TON = 2

    def get_value(self) -> str:
        return str(self.value)


