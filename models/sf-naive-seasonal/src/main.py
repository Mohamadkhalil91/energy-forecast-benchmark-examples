import os
from datetime import timedelta

import pandas as pd
from pandas import Timedelta
from statsforecast.models import SeasonalNaive
from enfobench import AuthorInfo, ModelInfo, ForecasterType
from enfobench.evaluation.server import server_factory
from enfobench.evaluation.utils import create_forecast_index


def periods_in_duration(ts, duration) -> int:
    if isinstance(duration, timedelta):
        duration = Timedelta(duration)

    first_delta = ts[1] - ts[0]
    last_delta = ts[-1] - ts[-2]
    assert first_delta == last_delta, "Season length is not constant"

    periods = duration / first_delta
    assert periods.is_integer(), "Season length is not a multiple of the frequency"

    return int(periods)


class NaiveSeasonal:

    def __init__(self, season_length: str):
        self.season_length = season_length.upper()

    def info(self) -> ModelInfo:
        return ModelInfo(
            name=f"Statsforecast.SeasonalNaive.{self.season_length}",
            authors=[
                AuthorInfo(
                    name="Attila Balint",
                    email="attila.balint@kuleuven.be"
                )
            ],
            type=ForecasterType.quantile,
            params={
                "seasonality": self.season_length,
            },
        )

    def forecast(
        self,
        horizon: int,
        history: pd.DataFrame,
        past_covariates: pd.DataFrame | None = None,
        future_covariates: pd.DataFrame | None = None,
        level: list[int] | None = None,
        **kwargs
    ) -> pd.DataFrame:
        # Create model using period length
        y = history.y
        periods = periods_in_duration(ts=y.index, duration=pd.Timedelta(self.season_length))
        model = SeasonalNaive(season_length=periods)

        # Make forecast
        pred = model.forecast(
            y=y.values,
            h=horizon,
            level=level,
            **kwargs
        )

        # Create index for forecast
        index = create_forecast_index(history=history, horizon=horizon)

        # Format forecast dataframe
        forecast = (
            pd.DataFrame(
                index=index,
                data=pred
            )
            .rename(columns={"mean": "yhat"})
            .fillna(y.mean())
        )
        return forecast


# Load parameters
seasonality = str(os.getenv("ENFOBENCH_MODEL_SEASONALITY"))

# Instantiate your model
model = NaiveSeasonal(seasonality)
# Create a forecast server by passing in your model
app = server_factory(model)
