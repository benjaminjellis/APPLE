from pathlib import Path
import plotly.express as px
from analytics.results import calculate_accuracy_transform
from core.loaders import load_json_or_csv
from IPython.display import display


class Visualisation(object):

    def __init__(self,show_visualisations: bool,use_strudel: bool = False, aggregated_data_filepath: str = None):
        """
        :param use_strudel: bool
                Default: False
                Whether to get aggregated results from STRUDEL or to use a local file
        :param aggregated_data_filepath: str
                Optional - Required if use_strudel is False
                filepath of aggregated results file to update
        """
        self.show_visualisations = show_visualisations
        if use_strudel:
            # Need to add somehting here using the STRUDEL interface to get up to date aggreagted results.
            # once got from strudel save locally
            # load then use calculate_accuracy_transform
            raise ValueError("Visualisation class does not yet support use of STRUDEl")
        else:
            # define path
            self.path = str(Path().absolute())
            # user loader to load aggregated results file
            self.aggregated_results = load_json_or_csv(self.path + "/" + aggregated_data_filepath)
            # use calculate_accuracy_transform def to create the weekly summed
        self.weekly_summed = calculate_accuracy_transform(self.aggregated_results, mode = "weekly")

    def predictor_team_history(self, predictor: str, team: str) -> None:
        """
        Showss a user's predictions involving a given team in tabular format
        :param predictor: str
                    initials of predictor to show predictions for
        :param team: str
                    which team to show the predictor's prdictions for
        :return: nothing
        """
        f_df = self.aggregated_results[(self.aggregated_results["AwayTeam"] == team) | (
            self.aggregated_results["HomeTeam"] == team)]
        cols_to_display = ["Date", "Time", "Week", "HomeTeam", "AwayTeam", predictor + " Prediction"]
        df_to_display = f_df[cols_to_display]
        display(df_to_display)

    def volatility(self, output_filepath: str = None) -> None:
        """
        This VIOLIN plot uses the calculate_accuracy_transform def to
        transform the aggregated weekly results into a box plot that
        helps visualise the spread (or volatility) of predictions made
        :param output_filepath: str OPTIONAL
                if the output is required to be saved as an HTML file the output filepath
                can be specified
        :return: nothing
        """
        fig_violin = px.violin(self.weekly_summed,
                               y = "Accuracy of Predictions (%)",
                               x = "Predictor", points = "all",
                               box = True,
                               hover_data = self.weekly_summed.columns,
                               template = "simple_white")
        # set range of axes
        fig_violin.update_yaxes(range = [0, 100])
        if self.show_visualisations:
            fig_violin.show()
        if output_filepath:
            fig_violin.write_html(output_filepath, include_plotlyjs= "cdn", full_html = False)

    def time_series(self, output_filepath: str = None) -> None:
        fig_ts = px.line(self.weekly_summed,
                         x = "Week",
                         y = "Accuracy of Predictions (%)",
                         color = "Predictor",
                         hover_name = "Predictor")
        if self.show_visualisations:
            fig_ts.show()
        if output_filepath:
            fig_ts.write_html(output_filepath, include_plotlyjs= "cdn", full_html = False)

    def stratified_performance(self, metric: str, output_filepath: str = None) -> None:
        """
        :param metric: str
                "top 6 teams" or  "newly promoted teams"
        :param output_filepath: str
                OPTIONAL - only required if output to be saved as HTML file
                Absolute filepath that output will be saved to.
        :return: nothing
        """
        if metric == "top 6 teams":
            sp_filter = ["Arsenal", "Liverpool", "Chelsea", "Man City", "Man United", "Tottenham"]
        elif metric == "newly promoted teams":
            sp_filter = ["Leeds", 'Fulham', "West Brom"]
        else:
            raise AttributeError("Metric not recognised. Please try 'top 6 teams' or 'newly promoted teams")
        # filter the df
        f_df = self.aggregated_results[(self.aggregated_results["AwayTeam"].isin(sp_filter)) | (
            self.aggregated_results["HomeTeam"].isin(sp_filter))]
        # calculate the accuracy transform
        f_df_accuracy_transform = calculate_accuracy_transform(f_df, mode = "overall")
        fig_sp = px.bar_polar(f_df_accuracy_transform,
                              r = "Accuracy of Predictions (%)",
                              theta = "Predictor",
                              color = "Predictor",
                              template = "simple_white")
        if self.show_visualisations:
            fig_sp.show()
        if output_filepath:
            fig_sp.write_html(output_filepath, include_plotlyjs= "cdn", full_html = False)