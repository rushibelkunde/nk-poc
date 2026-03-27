import pandas as pd

DATASETS = {
    "sales": "data/nk_sales_data_2022_2026_feb.csv",
    "inventory": "data/nk_inventory_2022_2026_feb.csv",
    "receivables": "data/nk_receivables_2022_2026_feb.csv",
    "gst": "data/nk_gst_data_2022_2026_feb.csv"
}

def get_database_schema() -> str:
    """Reads the headers of the CSVs to provide schema context to the LLM."""
    schema = ""
    for name, path in DATASETS.items():
        try:
            df = pd.read_csv(path, nrows=0)
            schema += f"- Dataset '{name}' (path: '{path}'): Columns: {', '.join(df.columns.tolist())}\n"
        except Exception as e:
            print(f"[Warning] Could not read schema for {path}: {e}")
    return schema