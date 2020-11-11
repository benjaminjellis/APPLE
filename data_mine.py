from core.data_mining import MineOdds
from core.strudel_interface import StrudelInterface
from pathlib import Path


path = str(Path().absolute())

user_prediction_file_name = "/week8userpredictions.csv"

user_prediction_loc_rel = "/data/user_predictions/20_21/week8/"
user_prediction_loc_abs = path + user_prediction_loc_rel
user_prediction_dir = Path(user_prediction_loc_abs)
if not user_prediction_dir.exists():
    user_prediction_dir.mkdir(parents = True)


sic = StrudelInterface(credentials_filepath = "credentials/credentials.json")
sic.get_fixtures_and_user_predictions(start_date = "2020-11-06", end_date = "2020-11-11", output_loc = user_prediction_loc_abs + user_prediction_file_name)

miner = MineOdds(fixtures_file = user_prediction_loc_rel + user_prediction_file_name,
                 mined_data_output = "data/mined_data/20_21/week8.json")

miner.all()

# a = sic.upload_mined_data(name = "test_5", mined_data_to_upload = data)
