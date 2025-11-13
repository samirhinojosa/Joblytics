from app.core.settings import get_settings
from app.core.logging_config import setup_logging
from app.infrastructure.ingestion.linkedin_scrapper import LinkedInScrapper, TimePosted


def main():
    settings = get_settings(LOG_LEVEL="INFO")
    setup_logging(settings)

    print("POSTGRES_USER from settings:", settings.POSTGRES_USER)
    print("Resolved log file:", settings.resolve_log_file())

    linkedin_scrapper = LinkedInScrapper(
        title="Python", location="Grenoble", time_posted=TimePosted.WEEK
    )

    jobs_summary = linkedin_scrapper.fetch_offers_summary()
    jobs_details = linkedin_scrapper.fetch_offers_details(jobs_summary)

    import pandas as pd

    pd.set_option("display.max_colwidth", 30)  # máximo 100 caracteres por celda
    pd.set_option("display.width", 100)  # ancho máximo total de la tabla
    pd.set_option("display.max_columns", None)  # mostrar todas las columnas
    pd.set_option("display.expand_frame_repr", False)  # no dividir en varias líneas

    def truncate_df(df: pd.DataFrame, max_len: int = 40) -> pd.DataFrame:
        def _truncate_value(x):
            s = str(x)
            return s if len(s) <= max_len else s[: max_len - 1] + "…"

        return df.applymap(_truncate_value)

    df = pd.DataFrame(jobs_details)
    df_trunc = truncate_df(df, max_len=30)
    print(df_trunc.drop(columns=["url", "description"]).to_markdown(index=False))


if __name__ == "__main__":
    main()
