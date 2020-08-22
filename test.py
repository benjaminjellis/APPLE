from core.weekly_batch import WeeklyBatch

weekly_run = WeeklyBatch(fixtures_to_predict = "data/user_predictions/19_20/week29/week29up.csv",
                         data_for_predictions = "data/mined_data/19_20/w29f.csv",
                         job_name = "test")
weekly_run.run(backtest = False, cleanup = True)


