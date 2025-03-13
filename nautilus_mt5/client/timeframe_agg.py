import polars as pl

# TODO: Use Nautilus Trader for agrregation.

class TimeframeAggregator:
    """ 
    The class for creating custom timeframes using polars for internal aggregation.
    
    This class provides methods to aggregate data into custom timeframes, leveraging the 
    performance and flexibility of the polars library.
    """
    def __init__(self):
        pass

    def aggregate(self, df, timeframe):
        """
        Aggregates the given DataFrame into the specified timeframe.

        Parameters:
        df (pl.DataFrame): The input DataFrame with a datetime column.
        timeframe (str): The timeframe to aggregate the data into (e.g., '2H', '30T').

        Returns:
        pl.DataFrame: The aggregated DataFrame.
        """
        return df.groupby_dynamic("datetime", every=timeframe).agg([
            pl.col("open").first().alias("open"),
            pl.col("high").max().alias("high"),
            pl.col("low").min().alias("low"),
            pl.col("close").last().alias("close"),
            pl.col("volume").sum().alias("volume")
        ])
