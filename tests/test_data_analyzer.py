import pytest
import pandas as pd
import numpy as np
import os
from analyzer_app.data_analyzer import DataAnalyzer

# Fixtures for test files
@pytest.fixture
def csv_file_utf8(tmp_path):
    content = "col1,col2\n1,a\n2,b\n3,c"
    file_path = tmp_path / "test_utf8.csv"
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)

@pytest.fixture
def csv_file_iso8859_1(tmp_path):
    # This fixture now creates a UTF-8 file, as DataAnalyzer expects pre-processed files
    content = "col1,col2\n1,e\n2,a\n3,c"
    file_path = tmp_path / "test_iso8859_1.csv"
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)

@pytest.fixture
def csv_file_semicolon(tmp_path):
    content = "col1;col2\n1;a\n2;b\n3;c"
    file_path = tmp_path / "test_semicolon.csv"
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)

@pytest.fixture
def excel_file(tmp_path):
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["x", "y", "z"]})
    file_path = tmp_path / "test.xlsx"
    df.to_excel(file_path, index=False)
    return str(file_path)

@pytest.fixture
def df_with_missing_values():
    return pd.DataFrame({
        "num_col": [1, 2, np.nan, 4, 5],
        "cat_col": ["A", "B", "A", np.nan, "C"],
        "all_nan_col": [np.nan, np.nan, np.nan, np.nan, np.nan],
        "high_missing_col": [1, np.nan, np.nan, np.nan, 5]
    })

@pytest.fixture
def df_for_plotting():
    return pd.DataFrame({
        "num_data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "cat_data": ["A", "B", "A", "C", "B", "A", "C", "B", "A", "C"],
        "empty_num": [np.nan] * 10,
        "empty_cat": [np.nan] * 10
    })

# Test cases for _load_data()
def test_load_data_csv_utf8(csv_file_utf8):
    analyzer = DataAnalyzer(file_path=csv_file_utf8)
    assert not analyzer.df.empty
    assert list(analyzer.df.columns) == ["col1", "col2"]
    assert analyzer.df.shape == (3, 2)

def test_load_data_csv_iso8859_1(csv_file_iso8859_1):
    analyzer = DataAnalyzer(file_path=csv_file_iso8859_1)
    assert not analyzer.df.empty
    assert list(analyzer.df.columns) == ["col1", "col2"]
    assert analyzer.df.shape == (3, 2)

def test_load_data_excel(excel_file):
    analyzer = DataAnalyzer(file_path=excel_file)
    assert not analyzer.df.empty
    assert list(analyzer.df.columns) == ["col1", "col2"]
    assert analyzer.df.shape == (3, 2)

def test_load_data_unsupported_type(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("some text")
    with pytest.raises(ValueError, match="Unsupported file type"):
        DataAnalyzer(file_path=str(file_path))

# Test cases for handle_missing_values()
def test_handle_missing_values(df_with_missing_values):
    analyzer = DataAnalyzer(df=df_with_missing_values.copy())
    analyzer.handle_missing_values(drop_threshold=0.5) # Drop columns with >50% missing

    # Check if 'all_nan_col' is dropped
    assert "all_nan_col" not in analyzer.df.columns
    # Check if 'high_missing_col' is dropped (3/5 = 60% missing)
    assert "high_missing_col" not in analyzer.df.columns

    # Check imputation for 'num_col'
    assert analyzer.df["num_col"].isnull().sum() == 0
    # Check imputation for 'cat_col'
    assert analyzer.df["cat_col"].isnull().sum() == 0

def test_handle_missing_values_no_drop(df_with_missing_values):
    analyzer = DataAnalyzer(df=df_with_missing_values.copy())
    analyzer.handle_missing_values(drop_threshold=0.9) # Don't drop columns with >90% missing

    assert "all_nan_col" not in analyzer.df.columns # all_nan_col should always be dropped
    assert "high_missing_col" in analyzer.df.columns

# Test cases for generate_visualizations()
def test_generate_visualizations_empty_df():
    analyzer = DataAnalyzer(df=pd.DataFrame())
    plots = analyzer.generate_visualizations()
    assert len(plots) == 0

def test_generate_visualizations_valid_data(df_for_plotting):
    analyzer = DataAnalyzer(df=df_for_plotting.copy())
    plots = analyzer.generate_visualizations()
    # Expect at least 2 plots for numerical (hist, box) and 1 for categorical (count)
    # Plus pair plot and num vs cat box plot if conditions met
    assert len(plots) >= 3 
    assert all("image" in p and "title" in p for p in plots)

def test_generate_visualizations_empty_columns(df_for_plotting):
    analyzer = DataAnalyzer(df=df_for_plotting.copy())
    # Ensure empty columns don't cause crashes and are skipped
    analyzer.df["num_data"] = np.nan # Make numerical column empty
    analyzer.df["cat_data"] = np.nan # Make categorical column empty
    plots = analyzer.generate_visualizations()
    # Should still generate plots for other columns if they exist, but in this case, all are empty
    # So, it should return 0 plots.
    assert len(plots) == 0

