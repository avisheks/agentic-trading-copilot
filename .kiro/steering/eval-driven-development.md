# Eval-Driven Development

All improvements to the trading copilot MVP must be validated against the existing evaluation suite.

## Rules

1. Run the current eval suite before adding any new component
2. Only merge changes that maintain or improve eval scores
3. Document baseline scores before starting work on a new feature
4. For feature enhacements, evaluation metrics should improve
5. For bug fixes, evaluation metrics should not regress
6. If a change degrades eval performance, it should not be added unless there's explicit justification

## Evaluation Command

```bash
#trading_copilot/.venv/bin/python trading_copilot/scripts/run_evaluation.py
trading_copilot/.venv/bin/python trading_copilot/scripts/run_statistical_evaluation.py    
```

## Workflow

1. Before implementing a new feature, run evals and record baseline metrics
2. Implement the feature
3. Run evals again and compare to baseline
4. Only proceed if metrics are maintained or improved

