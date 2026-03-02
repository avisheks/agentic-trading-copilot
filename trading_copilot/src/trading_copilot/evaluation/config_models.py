"""Configuration models for evaluation system."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class EvaluationParams:
    """Parameters for evaluation execution."""
    
    num_epochs: int = 5
    runs_per_epoch: int = 5
    max_parallelism: int = 3
    tickers: list[str] | None = None
    epoch_spacing_days: int = 21
    lookback_days: int = 14
    prediction_days: int = 7


@dataclass
class ReportConfig:
    """Configuration for evaluation reports."""
    
    format: str = "html"
    output_directory: str = "./reports"
    include_individual_runs: bool = False
    confidence_threshold: float = 0.0
    show_epoch_details: bool = True
    show_statistics: bool = True


@dataclass
class LoggingConfig:
    """Configuration for evaluation logging."""
    
    level: str = "INFO"
    show_progress: bool = True
    log_individual_runs: bool = False


@dataclass
class EvaluationConfig:
    """Complete evaluation configuration."""
    
    evaluation: EvaluationParams
    report: ReportConfig
    logging: LoggingConfig
    
    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "EvaluationConfig":
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to evaluation_config.yaml
            
        Returns:
            EvaluationConfig instance
        """
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        eval_params = EvaluationParams(**data.get('evaluation', {}))
        report_config = ReportConfig(**data.get('report', {}))
        logging_config = LoggingConfig(**data.get('logging', {}))
        
        return cls(
            evaluation=eval_params,
            report=report_config,
            logging=logging_config,
        )