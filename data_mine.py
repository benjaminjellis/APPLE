from core.data_mining import MineOdds
from core.strudel_interface import StrudelInterface
from pathlib import Path
import json


path = str(Path().absolute())

user_prediction_file_name = "/week14userpredictions.csv"

user_prediction_loc_rel = "/data/user_predictions/20_21/week14/"
user_prediction_loc_abs = path + user_prediction_loc_rel
user_prediction_dir = Path(user_prediction_loc_abs)
if not user_prediction_dir.exists():
    user_prediction_dir.mkdir(parents = True)


sic = StrudelInterface(credentials_filepath = "credentials/credentials.json")
"""

sic.get_fixtures_and_user_predictions(start_date = "2020-12-18", end_date = "2020-12-22", output_loc = user_prediction_loc_abs + user_prediction_file_name)

miner = MineOdds(fixtures_file = user_prediction_loc_rel + user_prediction_file_name,
                 mined_data_output = "data/mined_data/20_21/week14.json")

miner.all()

"""
with open("data/mined_data/20_21/week14.json") as json_file:
    data = json.load(json_file)
a = sic.upload_mined_data(name = "week14_2", mined_data_to_upload = data)
print(a)
