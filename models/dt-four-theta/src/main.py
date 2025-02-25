import os

import pandas as pd
from darts import TimeSeries
from darts.models import FourTheta
from enfobench import AuthorInfo, ModelInfo, ForecasterType
from enfobench.evaluation.server import server_factory
from enfobench.evaluation.utils import periods_in_duration


class FourThetaModel:

    def __init__(self, seasonality: str):
        self.seasonality = seasonality

    def info(self) -> ModelInfo:
        return ModelInfo(
            name=f"Darts.FourTheta.{self.seasonality}",
            authors=[
                AuthorInfo(
                    name="Attila Balint",
                    email="attila.balint@kuleuven.be"
                )
            ],
            type=ForecasterType.point,
            params={
                "seasonality": self.seasonality,
            },
        )

    def forecast(
        self,
        horizon: int,
        history: pd.DataFrame,
        past_covariates: pd.DataFrame | None = None,
        future_covariates: pd.DataFrame | None = None,
        **kwargs
    ) -> pd.DataFrame:
        seasonality_period = periods_in_duration(history.index, duration=self.seasonality)
        model = FourTheta(seasonality_period=seasonality_period)

        series = TimeSeries.from_dataframe(history, value_cols=['y'])
        model.fit(series)

        # Make forecast
        pred = model.predict(horizon)

        forecast = (
            pred.pd_dataframe()
            .rename(columns={"y": "yhat"})
            .fillna(history['y'].mean())
        )
        return forecast


seasonality = os.getenv("ENFOBENCH_MODEL_SEASONALITY")

# Instantiate your model
model = FourThetaModel(seasonality)

# Create a forecast server by passing in your model
app = server_factory(model)
