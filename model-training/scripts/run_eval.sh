#!/bin/bash

# Run model evaluation

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <eval_dataset_path> [source_documents_path]"
    echo ""
    echo "Example:"
    echo "  $0 /app/data/eval/eval.jsonl /app/data/eval/sources.json"
    exit 1
fi

EVAL_DATASET=$1
SOURCE_DOCS=${2:-}

echo "Starting model evaluation..."
echo "Evaluation Dataset: $EVAL_DATASET"
if [ -n "$SOURCE_DOCS" ]; then
    echo "Source Documents: $SOURCE_DOCS"
fi

# Create output directory
mkdir -p /tmp/eval_reports

# Run evaluation
python -c "
import sys
import json
import asyncio
from pathlib import Path
from app.evaluation.benchmark_suite import BenchmarkSuite
from app.evaluation.metrics_reporter import MetricsReporter

async def run_eval():
    print('Loading evaluation dataset...')

    eval_data = []
    with open('$EVAL_DATASET', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                eval_data.append(json.loads(line))

    print(f'Loaded {len(eval_data)} evaluation samples')

    if not eval_data:
        print('Error: Evaluation dataset is empty', file=sys.stderr)
        sys.exit(1)

    # Generate dummy predictions (in production, load from actual model)
    predictions = [item.get('output', 'Model response') for item in eval_data]

    # Load source documents if provided
    sources = None
    if '$SOURCE_DOCS':
        try:
            with open('$SOURCE_DOCS', 'r', encoding='utf-8') as f:
                sources = json.load(f)
            print(f'Loaded {len(sources)} source documents')
        except Exception as e:
            print(f'Warning: Failed to load source documents: {e}', file=sys.stderr)

    # Run benchmark
    print('Running benchmark suite...')
    benchmark = BenchmarkSuite()
    results = await asyncio.to_thread(
        benchmark.run_complete_benchmark,
        '$EVAL_DATASET',
        predictions,
        sources,
    )

    # Generate reports
    print('Generating reports...')
    reporter = MetricsReporter()

    # JSON report
    json_report = reporter.generate_json_report(
        results.get('metrics', {}),
        'evaluation_run',
        '/tmp/eval_reports/results.json'
    )

    # Markdown report
    md_report = reporter.generate_markdown_report(
        results.get('metrics', {}),
        'evaluation_run',
        '/tmp/eval_reports/report.md'
    )

    # Print summary
    print()
    print('=' * 80)
    print('EVALUATION SUMMARY')
    print('=' * 80)

    if 'metrics' in results:
        metrics = results['metrics']

        if 'qa_metrics' in metrics:
            qa = metrics['qa_metrics']
            print(f\"Exact Match: {qa.get('exact_match', 0):.2%}\")
            print(f\"F1 Score: {qa.get('f1', 0):.4f}\")
            print(f\"BLEU: {qa.get('bleu', 0):.4f}\")

        if 'quality_metrics' in metrics:
            qual = metrics['quality_metrics']
            print(f\"Overall Quality: {qual.get('overall', 0):.2f} / 5.0\")

        if 'hallucination_metrics' in metrics:
            hal = metrics['hallucination_metrics']
            print(f\"Hallucination Rate: {hal.get('average_hallucination_rate', 0):.2%}\")

    print()
    print('Reports saved to /tmp/eval_reports/')

asyncio.run(run_eval())
"

echo "Evaluation complete!"
