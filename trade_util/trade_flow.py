from trade_util.base import FilterBase


class TradeFlow(FilterBase):
    IMPORT = 1
    EXPORT = 2

    def get_value(self) -> str:
        return str(self.value)
