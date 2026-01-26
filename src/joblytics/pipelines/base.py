import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any


class BasePipeline(ABC):
    def __init__(self, pdf_path: Path, poll_type: str):
        """
        Initialise le processus du pipeline.

        Args:
            file : Path
                Chemin absolu vers le fichier PDF à analyser.
            poll_type : str
               Identifiant du type de sondage (ex. "pt4").
        """

        self.logger = logging.getLogger("joblytics")

    @abstractmethod
    def extract(self) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        pass

    @abstractmethod
    def build(self) -> int:
        pass

    def run(self):
        """
        Exécute le pipeline complet.

        Étapes d’exécution :
        1. Validation du fichier `metadata.txt`.
        2. Nettoyage des fichiers de sortie existants.
        3. Extraction des données depuis la source.
        4. Construction et écriture des artefacts finaux.

        Toute erreur rencontrée durant l’exécution est journalisée puis relancée.
        """
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
