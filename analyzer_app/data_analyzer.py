import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import os
import io
import base64
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer

warnings.filterwarnings('ignore')

class DataAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = self._load_data()

    def _load_data(self):
        """Loads data from a CSV file, trying common encodings."""
        try:
            return pd.read_csv(self.file_path)
        except UnicodeDecodeError:
            try:
                return pd.read_csv(self.file_path, encoding='ISO-8859-1')
            except Exception as e:
                print(f"Error loading file with ISO-8859-1 encoding: {e}")
                raise
        except Exception as e:
            print(f"Error loading file: {e}")
            raise

    def summarize_data(self):
        """Provides a comprehensive summary of the dataframe."""
        print(f"\n--- Summary for {self.file_path} ---")
        print("\nData Info:")
        self.df.info()
        print("\nMissing Values:")
        print(self.df.isnull().sum())
        print("\nDescriptive Statistics:")
        print(self.df.describe())

    def handle_missing_values(self, drop_threshold=0.7):
        """
        Handles missing values:
        - Converts common string placeholders to NaN.
        - Drops columns with missing values exceeding a threshold.
        - Imputes numerical columns with mean.
        - Imputes categorical columns with mode.
        """
        print("\n--- Handling Missing Values ---")
        # Convert common string placeholders to NaN
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                self.df[col] = self.df[col].replace(['?', 'missing', 'Missing', 'NaN', 'nan', 'N/A', 'None'], np.nan)

        # Drop columns with too many missing values
        initial_cols = self.df.shape[1]
        self.df.dropna(axis=1, thresh=int(self.df.shape[0] * (1 - drop_threshold)), inplace=True)
        if self.df.shape[1] < initial_cols:
            print(f"Dropped {initial_cols - self.df.shape[1]} columns due to high missing value percentage.")

        # Impute remaining missing values
        for col in self.df.columns:
            if self.df[col].isnull().any():
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    self.df[col].fillna(self.df[col].mean(), inplace=True)
                    print(f"Imputed missing values in numerical column '{col}' with mean.")
                else:
                    # Use SimpleImputer for categorical mode imputation to handle potential empty series from mode()
                    imputer = SimpleImputer(strategy='most_frequent')
                    self.df[col] = imputer.fit_transform(self.df[[col]]).ravel()
                    print(f"Imputed missing values in categorical column '{col}' with mode.")
        print("Missing values handled.")

    def convert_datatypes(self):
        """
        Converts columns to appropriate data types.
        - Removes non-numeric characters from potentially numeric columns.
        - Converts columns to numeric where possible.
        - Converts float columns to int if all values are integers.
        """
        print("\n--- Converting Data Types ---")
        for col in self.df.columns:
            # Try to clean and convert to numeric
            if self.df[col].dtype == 'object':
                # Remove common non-numeric characters
                cleaned_col = self.df[col].astype(str).str.replace(r'[$,+%]', '', regex=True).str.strip()
                
                # Attempt to convert to numeric
                converted_numeric = pd.to_numeric(cleaned_col, errors='coerce')
                
                # If a significant portion could be converted, update the column
                if converted_numeric.notna().sum() > 0.5 * len(self.df): # More than half are convertible
                    self.df[col] = converted_numeric
                    print(f"Converted column '{col}' to numeric.")
            
            # Convert float to int if all values are integers
            if pd.api.types.is_float_dtype(self.df[col]) and not self.df[col].isnull().any() and (self.df[col] == self.df[col].astype(int)).all():
                self.df[col] = self.df[col].astype(int)
                print(f"Converted float column '{col}' to integer.")
        print("Data types converted.")

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
        """
        print("\n--- Generating Visualizations ---")
        plots = []

        # Numerical columns
        numerical_cols = self.df.select_dtypes(include=np.number).columns
        for col in numerical_cols:
            # Histogram
            plt.figure(figsize=(10, 6))
            sns.histplot(data=self.df, x=col, kde=True)
            plt.title(f'Distribution of {col}')
            plt.xlabel(col)
            plt.ylabel('Frequency')
            plt.tight_layout()
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plots.append({'title': f'Distribution of {col}', 'image': base64.b64encode(buf.getvalue()).decode('utf-8')})
            plt.close()

            # Box plot
            plt.figure(figsize=(10, 6))
            sns.boxplot(data=self.df, y=col)
            plt.title(f'Box Plot of {col}')
            plt.ylabel(col)
            plt.tight_layout()
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plots.append({'title': f'Box Plot of {col}', 'image': base64.b64encode(buf.getvalue()).decode('utf-8')})
            plt.close()

        # Categorical columns
        categorical_cols = self.df.select_dtypes(include='object').columns
        for col in categorical_cols:
            plt.figure(figsize=(10, 6))
            sns.countplot(data=self.df, x=col)
            plt.title(f'Count of {col}')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plots.append({'title': f'Count of {col}', 'image': base64.b64encode(buf.getvalue()).decode('utf-8')})
            plt.close()

        # Pair plot for a subset of numerical columns
        if len(numerical_cols) > 1:
            subset_cols = numerical_cols[:min(len(numerical_cols), 5)] # Limit to first 5 for pair plot
            if len(subset_cols) > 1:
                plt.figure(figsize=(12, 10))
                sns.pairplot(self.df[subset_cols])
                plt.suptitle('Pair Plot of Numerical Features', y=1.02)
                plt.tight_layout()
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plots.append({'title': 'Pair Plot of Numerical Features', 'image': base64.b64encode(buf.getvalue()).decode('utf-8')})
                plt.close()

        # Numerical vs Categorical Box plots (if suitable columns exist)
        if len(numerical_cols) > 0 and len(categorical_cols) > 0:
            num_col = numerical_cols[0] # Take the first numerical column
            cat_col = categorical_cols[0] # Take the first categorical column
            if self.df[cat_col].nunique() < 20: # Only if not too many categories
                plt.figure(figsize=(12, 7))
                sns.boxplot(data=self.df, x=cat_col, y=num_col)
                plt.title(f'{num_col} by {cat_col}')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plots.append({'title': f'{num_col} by {cat_col}', 'image': base64.b64encode(buf.getvalue()).decode('utf-8')})
                plt.close()
        
        print("Visualizations generated.")
        return plots

    def run_analysis(self):
        """Runs the full data cleaning and analysis pipeline."""
        self.summarize_data()
        self.handle_missing_values()
        self.convert_datatypes()
        self.handle_outliers()
        self.encode_categoricals()
        self.summarize_data() # Summarize again after cleaning
        plots = self.generate_visualizations()
        print(f"\nAnalysis complete.")
        return plots

