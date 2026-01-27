import logging
from dataclasses import dataclass


from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any

@dataclass(frozen=True)
class PipelineReport:
    provider: str
    produced: int
    loaded: int
    started_at: datetime
    finished_at: datetime
    errors: tuple[str, ...] = ()


class BasePipeline(ABC):
    def __init__(self, pdf_path: Path, poll_type: str):
        self.logger = logging.getLogger("joblytics")

    def _validate_inputs(self) -> None:
        """
        Valide les paramètres fournis au constructeur.

        Vérifie que :
        - `pdf_path` est une instance de pathlib.Path et que le fichier existe.
        - `poll_type` est une chaîne de caractères valide.
        """
        if not isinstance(self.pdf_path, Path):
            self.logger.error("Le paramètre 'pdf_path' doit être une instance de pathlib.Path.")
            raise TypeError("Le paramètre 'pdf_path' doit être une instance de pathlib.Path.")
        if not self.pdf_path.exists():
            self.logger.error(f"Le fichier spécifié est introuvable : {self.pdf_path}")
            raise FileNotFoundError(f"Le fichier spécifié est introuvable : {self.pdf_path}")
        if not isinstance(self.poll_type, str):
            self.logger.error("Le paramètre 'poll_type' doit être une chaîne de caractères.")
            raise TypeError("Le paramètre 'poll_type_id' doit être une chaîne de caractères.")

    @abstractmethod
    def extract(self) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        pass

    @abstractmethod
    def build(self) -> int:
        pass

    def run(self):
        try:
            self.logger.info("🔍  Détection et extraction des pages de données... ")
            self.logger.info("=" * 70)
            survey_metadata, surveys = self.extract()
            self.logger.info("")

            self.logger.info("📦  Extraction et construction des CSV...")
            self.logger.info("=" * 70)
            nb_csv_created = self.build(survey_metadata, surveys)
            self.logger.info("")

            self.logger.info("=" * 70)
            self.logger.info(f"✅  {nb_csv_created} fichier(s) CSV généré(s)")
            self.logger.info("")

        except FileNotFoundError as e:
            self.logger.error(f"Erreur de configuration : {e}")
            raise

        except Exception as e:
            self.logger.error(f"Erreur inattendue dans le pipeline : {e}")
            raise
