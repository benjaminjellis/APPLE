from analytics.results import Results

Results(user_predictions =  "data/user_predictions/20_21/week5/week5userpredictions.csv",
        apple_predictions =
        "results/20_21/week5/7640a728-04fb-11eb-8c32-acde48001122_predicted_results.csv").aggregate(
        ftrs = "data/ftrs/20_21/week5/ftrs.csv",
        winners_log = "data/aggregated_results/20_21/winners_log.csv",
        aggregated_results_file = "data/aggregated_results/20_21/predictions_and_results_log.csv")
