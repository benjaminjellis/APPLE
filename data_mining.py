from core.miners import MineOdds


miner = MineOdds(fixtures_file = "data/user_predictions/20_21/week7/week7userpredictions.csv", \
                 mined_data_output = "data/mined_data/20_21/week7.json")

miner.all()