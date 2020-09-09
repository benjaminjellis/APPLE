"""
This script is used to generate predictions using APPLE
"""

from core.APPLE import APPLE


# fixtures APPLE will predict results for
fixtures_to_predict = "data/user_predictions/20_21/week1/week1userpredictions.csv"
# data APPLE will use to make predictions
data_for_predictions = "data/mined_data/20_21/week1.csv"
# data for APPLE to use to backtest saved models
data_to_backtest_on = ["data/mined_data/19_20/w29f.csv"]
ftrs = ["data/ftrs/19_20/week29res.csv"]

# create an instance of APPLE called "weekly_run"
weekly_run = APPLE(fixtures_to_predict = fixtures_to_predict,
                   data_for_predictions = data_for_predictions,
                   job_name = "week1")

# use weekly run to backtest the saved models
# weekly_run.backtest(data_to_backtest_on = data_to_backtest_on, ftrs = ftrs)

# use weekly run to make the predictions
weekly_run.run()

# use weekly run to cleanup saved models dir
weekly_run.cleanup()