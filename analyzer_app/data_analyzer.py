import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import os
import io
import base64
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer

warnings.filterwarnings('ignore')

class DataAnalyzer:
    def __init__(self, file_path=None, df=None):
        if file_path:
            self.file_path = file_path
            self.df = self._load_data()
        elif df is not None:
            self.df = df
        else:
            raise ValueError("Either file_path or df must be provided.")

    def _load_data(self):
        """Loads data from the specified file path, supporting CSV and Excel."""
        file_extension = os.path.splitext(self.file_path)[1].lower()
        try:
            if file_extension == '.csv':
                # In views.py, we're already handling encoding and delimiter detection
                # and saving to a temp CSV. So, we can just read it directly here.
                return pd.read_csv(self.file_path)
            elif file_extension in ['.xls', '.xlsx']:
                return pd.read_excel(self.file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
        except Exception as e:
            logging.error(f"Error loading file {self.file_path}: {e}")
            raise

    def summarize_data(self):
        """Provides a comprehensive summary of the dataframe and returns it as a dictionary."""
        summaries = {}

        # Data Info
        buf = io.StringIO()
        self.df.info(buf=buf)
        summaries['data_info'] = buf.getvalue()

        # Missing Values
        summaries['missing_values'] = self.df.isnull().sum().to_frame('count').to_html()

        # Descriptive Statistics
        summaries['descriptive_statistics'] = self.df.describe().to_html()

        return summaries

    def handle_missing_values(self, drop_threshold=0.7):
        """
        Handles missing values:
        - Converts common string placeholders to NaN.
        - Drops columns with missing values exceeding a threshold.
        - Imputes numerical columns with mean.
        - Imputes categorical columns with mode.
        """
        logging.info("--- Handling Missing Values ---")
        
        # Convert common string placeholders to NaN
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                initial_nan_count = self.df[col].isnull().sum()
                self.df[col] = self.df[col].replace(['?', 'missing', 'Missing', 'NaN', 'nan', 'N/A', 'None', ''], np.nan)
                if self.df[col].isnull().sum() > initial_nan_count:
                    logging.info(f"Converted string placeholders to NaN in column '{col}'.")

        # Drop columns with too many missing values
        initial_cols = self.df.shape[1]
        cols_to_keep = []
        for col in self.df.columns:
            missing_percentage = self.df[col].isnull().sum() / len(self.df)
            if missing_percentage <= drop_threshold:
                cols_to_keep.append(col)
            else:
                logging.info(f"Column '{col}' dropped due to high missing value percentage ({missing_percentage*100:.2f}% missing).")
        self.df = self.df[cols_to_keep]
        if self.df.shape[1] < initial_cols:
            dropped_cols_count = initial_cols - self.df.shape[1]
            logging.info(f"Dropped {dropped_cols_count} columns due to high missing value percentage (>{drop_threshold*100}% missing).")
        
        # Impute remaining missing values
        for col in self.df.columns:
            if self.df[col].isnull().any():
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    if not self.df[col].isnull().all(): # Only impute if not all values are NaN
                        self.df[col] = self.df[col].fillna(self.df[col].mean())
                        logging.info(f"Imputed missing values in numerical column '{col}' with mean.")
                    else:
                        logging.warning(f"Column '{col}' is entirely NaN and cannot be imputed with mean. Consider dropping or alternative handling.")
                else:
                    # Use SimpleImputer for categorical mode imputation to handle potential empty series from mode()
                    if not self.df[col].isnull().all(): # Only impute if not all values are NaN
                        imputer = SimpleImputer(strategy='most_frequent')
                        self.df[col] = imputer.fit_transform(self.df[[col]]).ravel()
                        logging.info(f"Imputed missing values in categorical column '{col}' with mode.")
                    else:
                        logging.warning(f"Column '{col}' is entirely NaN and cannot be imputed with mode. Consider dropping or alternative handling.")
        logging.info("Missing values handled.")

    def convert_datatypes(self):
        """
        Converts columns to appropriate data types.
        - Removes non-numeric characters from potentially numeric columns.
        - Converts columns to numeric where possible.
        - Converts float columns to int if all values are integers.
        """
        logging.info("--- Converting Data Types ---")
        for col in self.df.columns:
            # Try to convert to datetime first
            if self.df[col].dtype == 'object':
                try:
                    converted_datetime = pd.to_datetime(self.df[col], errors='coerce')
                    if not converted_datetime.isnull().all():
                        self.df[col] = converted_datetime
                        logging.info(f"Converted column '{col}' to datetime.")
                        continue # Skip to next column if successfully converted to datetime
                except Exception as e:
                    logging.debug(f"Could not convert column '{col}' to datetime: {e}")

            # Try to clean and convert to numeric
            if self.df[col].dtype == 'object':
                # Remove common non-numeric characters
                cleaned_col = self.df[col].astype(str).str.replace(r'[$,+%]', '', regex=True).str.strip()
                
                # Attempt to convert to numeric
                converted_numeric = pd.to_numeric(cleaned_col, errors='coerce')
                
                # If a significant portion could be converted and it's not all NaNs, update the column
                if pd.api.types.is_numeric_dtype(converted_numeric) and converted_numeric.notna().sum() > 0.5 * len(self.df) and not converted_numeric.isnull().all():
                    self.df[col] = converted_numeric
                    logging.info(f"Converted column '{col}' to numeric.")
                elif converted_numeric.isnull().all():
                    logging.warning(f"Column '{col}' became entirely NaN after numeric conversion attempt. Keeping as object.")

            # Convert float to int if all values are integers and not all are NaN
            if pd.api.types.is_float_dtype(self.df[col]) and not self.df[col].isnull().all() and (self.df[col].dropna() == self.df[col].dropna().astype(int)).all():
                self.df[col] = self.df[col].astype(int)
                logging.info(f"Converted float column '{col}' to integer.")
        logging.info("Data types converted.")

    def handle_outliers(self, lower_percentile=0.05, upper_percentile=0.95):
        """
        Handles outliers by capping/flooring numerical columns.
        """
        print("\n--- Handling Outliers ---")
        for col in self.df.select_dtypes(include=np.number).columns:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            # Cap/Floor outliers
            self.df[col] = np.where(self.df[col] < lower_bound, self.df[col].quantile(lower_percentile), self.df[col])
            self.df[col] = np.where(self.df[col] > upper_bound, self.df[col].quantile(upper_percentile), self.df[col])
            print(f"Capped/floored outliers in numerical column '{col}'.")
        print("Outliers handled.")

    def encode_categoricals(self):
        """
        Encodes categorical columns using Label Encoding.
        Excludes columns that are likely unique identifiers (e.g., 'Name', 'ID', 'Product_ID').
        """
        print("\n--- Encoding Categorical Features ---")
        for col in self.df.select_dtypes(include='object').columns:
            # Heuristic to avoid encoding unique identifiers
            if self.df[col].nunique() > 0.8 * len(self.df) or 'name' in col.lower() or 'id' in col.lower():
                print(f"Skipping encoding for '{col}' (likely a unique identifier).")
                continue
            
            le = LabelEncoder()
            self.df[col] = le.fit_transform(self.df[col])
            print(f"Label encoded column '{col}'.")
        print("Categorical features encoded.")

    def generate_visualizations(self):
        """
        Generates various visualizations and returns them as base64 encoded strings.
        Includes checks for sufficient data and improved aesthetics.
        """
        logging.info("--- Generating Visualizations ---")
        plots = []

        if self.df.empty:
            logging.warning("DataFrame is empty, skipping visualization generation.")
            return plots

        # Set a consistent style for all plots
        sns.set_style("whitegrid")
        plt.rcParams['figure.autolayout'] = True # Automatically adjust plot params for a tight layout

        # Numerical columns
        numerical_cols = self.df.select_dtypes(include=np.number).columns
        for col in numerical_cols:
            if self.df[col].dropna().empty:
                logging.warning(f"Numerical column '{col}' is empty or all NaN, skipping plots.")
                continue

            # Histogram
            try:
                plt.figure(figsize=(10, 6))
                sns.histplot(data=self.df, x=col, kde=True)
                plt.title(f'Distribution of {col.replace('_', ' ').title()}', fontsize=16)
                plt.xlabel(col.replace('_', ' ').title(), fontsize=12)
                plt.ylabel('Frequency', fontsize=12)
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plots.append({'title': f'Distribution of {col.replace('_', ' ').title()}', 'image': base64.b64encode(buf.getvalue()).decode('utf-8')})
                plt.close()
                logging.info(f"Generated histogram for {col}")
            except Exception as e:
                logging.error(f"Error generating histogram for {col}: {e}")
                plt.close()

            # Box plot
            try:
                plt.figure(figsize=(10, 6))
                sns.boxplot(data=self.df, y=col, orientation='vertical')
                plt.title(f'Box Plot of {col.replace('_', ' ').title()}', fontsize=16)
                plt.ylabel(col.replace('_', ' ').title(), fontsize=12)
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plots.append({'title': f'Box Plot of {col.replace('_', ' ').title()}', 'image': base64.b64encode(buf.getvalue()).decode('utf-8')})
                plt.close()
                logging.info(f"Generated box plot for {col}")
            except Exception as e:
                logging.error(f"Error generating box plot for {col}: {e}")
                plt.close()

        # Categorical columns
        categorical_cols = self.df.select_dtypes(include='object').columns
        for col in categorical_cols:
            if self.df[col].dropna().empty:
                logging.warning(f"Categorical column '{col}' is empty or all NaN, skipping plots.")
                continue
            if self.df[col].nunique() > 50: # Limit categories for readability
                logging.warning(f"Column '{col}' has too many unique categories ({self.df[col].nunique()}), skipping count plot.")
                continue

            try:
                plt.figure(figsize=(12, 7))
                sns.countplot(data=self.df, x=col, order=self.df[col].value_counts().index)
                plt.title(f'Count of {col.replace('_', ' ').title()}', fontsize=16)
                plt.xlabel(col.replace('_', ' ').title(), fontsize=12)
                plt.ylabel('Count', fontsize=12)
                plt.xticks(rotation=45, ha='right')
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plots.append({'title': f'Count of {col.replace('_', ' ').title()}', 'image': base64.b64encode(buf.getvalue()).decode('utf-8')})
                plt.close()
                logging.info(f"Generated count plot for {col}")
            except Exception as e:
                logging.error(f"Error generating count plot for {col}: {e}")
                plt.close()

        # Pair plot for a subset of numerical columns
        if len(numerical_cols) > 1:
            subset_cols = numerical_cols[:min(len(numerical_cols), 5)] # Limit to first 5 for pair plot
            # Ensure there's enough valid data for a pair plot
            plot_df = self.df[subset_cols].dropna()
            if not plot_df.empty and len(subset_cols) > 1:
                try:
                    plt.figure(figsize=(12, 10))
                    sns.pairplot(plot_df)
                    plt.suptitle('Pair Plot of Numerical Features', y=1.02, fontsize=18)
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png')
                    buf.seek(0)
                    plots.append({'title': 'Pair Plot of Numerical Features', 'image': base64.b64encode(buf.getvalue()).decode('utf-8')})
                    plt.close()
                    logging.info("Generated pair plot.")
                except Exception as e:
                    logging.error(f"Error generating pair plot: {e}")
                    plt.close()

        # Numerical vs Categorical Box plots (if suitable columns exist)
        if len(numerical_cols) > 0 and len(categorical_cols) > 0:
            num_col = numerical_cols[0] # Take the first numerical column
            cat_col = categorical_cols[0] # Take the first categorical column
            if self.df[cat_col].nunique() < 20: # Only if not too many categories
                try:
                    plt.figure(figsize=(12, 7))
                    sns.boxplot(data=self.df, x=cat_col, y=num_col)
                    plt.title(f'{num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}', fontsize=16)
                    plt.xlabel(cat_col.replace('_', ' ').title(), fontsize=12)
                    plt.ylabel(num_col.replace('_', ' ').title(), fontsize=12)
                    plt.xticks(rotation=45, ha='right')
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png')
                    buf.seek(0)
                    plots.append({'title': f'{num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}', 'image': base64.b64encode(buf.getvalue()).decode('utf-8')})
                    plt.close()
                    logging.info(f"Generated numerical vs categorical box plot for {num_col} by {cat_col}")
                except Exception as e:
                    logging.error(f"Error generating numerical vs categorical box plot for {num_col} by {cat_col}: {e}")
                    plt.close()
        
        logging.info("Visualizations generation complete.")
        return plots

    def run_analysis(self):
        """Runs the full data cleaning and analysis pipeline."""
        initial_summary = self.summarize_data()
        self.handle_missing_values()
        self.convert_datatypes()
        self.handle_outliers()
        self.encode_categoricals()
        final_summary = self.summarize_data() # Summarize again after cleaning
        plots = self.generate_visualizations()
        print(f"\nAnalysis complete.")
        return plots, {'initial': initial_summary, 'final': final_summary}
