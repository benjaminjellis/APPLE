from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from analytics.transforms import calculate_accuracy_transform, winners_from_dataframe
from core.loaders import load_json_or_csv
from IPython.display import display

pd.options.mode.chained_assignment = None


class Visualisation(object):

    def __init__(self, show_visualisations: bool, aggregated_data_filepath: str):
        """
        :param show_visualisations: bool
        :param aggregated_data_filepath: str
                Relative filepath of aggregated results file to load
        """
        self.show_visualisations = show_visualisations
        # define path
        self.path = str(Path().absolute())
        # user loader to load aggregated results file
        self.aggregated_results = load_json_or_csv(self.path + "/" + aggregated_data_filepath)
        # use calculate_accuracy_transform def to create the weekly summed
        self.weekly_summed = calculate_accuracy_transform(self.aggregated_results, mode = "weekly")
        self.total_summed = None

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
        """
        Time series plot of accuracy of each predictor for each week
        :param output_filepath: str
                OPTIONAL - only required if output to be saved as HTML file
                Absolute filepath that output will be saved to.
        :return: nothing
        """
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

    def weekly_winner(self, output_filepath: str = None) -> None:
        """
        Table showing results from the latest week
        :param output_filepath: str
                OPTIONAL - only required if output to be saved as HTML file
                Absolute filepath that output will be saved to.
        :return: nothing
        """
        weeks = self.weekly_summed["Week"].to_list()
        weeks = list(set(weeks))
        this_week = max(weeks)
        this_week_summed = self.weekly_summed[self.weekly_summed["Week"] == this_week]
        decimals = 1
        this_week_summed["Accuracy of Predictions (%)"] = this_week_summed["Accuracy of Predictions (%)"].apply(
            lambda x: round(x, decimals))
        this_week_summed = this_week_summed.sort_values(by = "Accuracy of Predictions (%)", ascending = False)
        fig = go.Figure(data = [go.Table(
            header = dict(values = list(this_week_summed.columns),
                          align = 'left'),
            cells = dict(values = [this_week_summed["Predictor"], this_week_summed["Correct Predictions"], this_week_summed["Week"], this_week_summed["Accuracy of Predictions (%)"]],
                         align = 'left'))
        ])
        winner = winners_from_dataframe(this_week_summed, find_max_of = "Accuracy of Predictions (%)", get_winners_from = "Predictor")
        if self.show_visualisations:
            fig.show()
        if output_filepath:
            fig.write_html(output_filepath, include_plotlyjs= "cdn", full_html = False)

    def total_winner(self, output_filepath: str = None) -> None:
        """
        Table showing total results
        :param output_filepath: str
                OPTIONAL - only required if output to be saved as HTML file
                Absolute filepath that output will be saved to.
        :return: nothing
        """
        self.total_summed = calculate_accuracy_transform(self.aggregated_results, mode = "overall")
        self.total_summed = self.total_summed.sort_values(by = "Accuracy of Predictions (%)", ascending = False)
        decimals = 1
        self.total_summed["Accuracy of Predictions (%)"] = self.total_summed["Accuracy of Predictions (%)"].apply(lambda x: round(x, decimals))
        fig = go.Figure(data = [go.Table(
            header = dict(values = list(self.total_summed.columns),
                          align = 'left'),
            cells = dict(values = [self.total_summed["Predictor"],
                                   self.total_summed["Correct Predictions"],
                                   self.total_summed["Accuracy of Predictions (%)"]],
                         align = 'left'))
        ])
        winner = winners_from_dataframe(self.total_summed, find_max_of = "Accuracy of Predictions (%)", get_winners_from = "Predictor")
        if self.show_visualisations:
            fig.show()
        if output_filepath:
            fig.write_html(output_filepath, include_plotlyjs = "cdn", full_html = False)
