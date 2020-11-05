from analytics.visulisation import Visualisation
from pathlib import Path
from core.strudel_interface import StrudelInterface
from datetime import datetime


request_id = "001_test"

path = str(Path().absolute())

# create temp data loc
temp_dir_str = path + "/temporary_data/" + request_id
temp_dir = Path(temp_dir_str)
if not temp_dir.exists():
    temp_dir.mkdir(parents = True)
# create STRUDEL connection to get f
# trs and predictions from start of the season up until today
strudel_connection = StrudelInterface(credentials_filepath = path + '/credentials/credentials.json')
# first day of the season
start_date = "2020-09-12"
end_date = datetime.today().strftime("%Y-%m-%d")
historical_data_loc = "temporary_data/" + request_id + "/historical_data.csv"
strudel_connection.get_predictions_and_ftrs(start_date= start_date,
                                            end_date = end_date,
                                            output_loc = historical_data_loc)
visualizer = Visualisation(aggregated_data_filepath = historical_data_loc, show_visualisations = True)
visualizer.weekly_winner()
visualizer.total_winner()
