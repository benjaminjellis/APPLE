"""
This script is used to generate predictions using APPLE
"""

from core.APPLE import APPLE


# fixtures APPLE will predict results for
fixtures_to_predict = "data/user_predictions/20_21/week5/week5userpredictions.csv"
# data APPLE will use to make predictions
data_for_predictions = "data/mined_data/20_21/week4data.json"

# data for APPLE to use to backtest saved models
# data_to_backtest_on = "data/mined_data/19_20/w29f.csv"
# ftrs = ["data/ftrs/19_20/week29res.csv"]

# create an instance of APPLE called "weekly_run", if you want to use STRUDEL
weekly_run = APPLE(use_strudel = True,
                   start_date = "2020-10-17",
                   end_date = "2020-10-20",
                   fixtures_to_predict = fixtures_to_predict,
                   data_for_predictions = data_for_predictions,
                   job_name = "week5",
                   week = 5)

# if you want to use a local file
""""
weekly_run = APPLE(use_strudel = False,
                   fixtures_to_predict = fixtures_to_predict,
                   data_for_predictions = data_for_predictions,
                   job_name = "week5",
                   week = 5)
"""

# use weekly run to backtest the saved models
# weekly_run.backtest(data_to_backtest_on = data_to_backtest_on, ftrs = ftrs)

# use weekly run to make the predictions
weekly_run.run()

# use weekly run to cleanup saved models dir
# weekly_run.cleanup()
