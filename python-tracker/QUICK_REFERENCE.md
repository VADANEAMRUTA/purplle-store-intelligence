# Evaluation Pipeline - Quick Reference

## Installation

```bash
# Update requirements
pip install -r requirements.txt

# Verify installation
python -c "import pandas, cv2, matplotlib, openpyxl; print('✅ All packages installed')"
```

## Generate Sample Files

```bash
python evaluate_pipeline.py --generate-sample
# Creates: sample_annotations.xlsx
```

## File Validation

```bash
# Validate videos in directory
python evaluation_utils.py validate-videos sample_video/videos

# Validate annotations file
python evaluation_utils.py validate-annotations ground_truth.xlsx sample_video/videos

# Create annotation template
python evaluation_utils.py create-template my_annotations.xlsx

# Get video metadata
python evaluation_utils.py video-info sample_video/videos/video1.mp4
```

## Run Complete Evaluation

```bash
# Default settings (IOU=0.5, confidence=0.5, all frames)
python evaluate_pipeline.py \
  --annotations ground_truth.xlsx \
  --videos sample_video/videos \
  --output evaluation_results

# With custom thresholds
python evaluate_pipeline.py \
  --annotations ground_truth.xlsx \
  --videos sample_video/videos \
  --output evaluation_results \
  --iou-threshold 0.5 \
  --confidence 0.5 \
  --max-frames 500
```

## Python API Usage

### 1. Parse Ground Truth

```python
from parse_ground_truth import GroundTruthParser

# Load and parse annotations
parser = GroundTruthParser('ground_truth.xlsx')
parser.load_annotations()
ground_truth = parser.parse_ground_truth()

# Get annotations for specific frame (with ±50ms tolerance)
annotations = parser.get_frame_annotations('video1.mp4', frame_ms=5000)

# Export parsed data to CSV
parser.export_to_csv('parsed_annotations.csv')
```

### 2. Run Evaluation

```python
from evaluate_with_ground_truth import PersonDetectionEvaluator
from detector import PersonDetector
from parse_ground_truth import GroundTruthParser

# Initialize evaluator
evaluator = PersonDetectionEvaluator(
    detector_class=PersonDetector,
    ground_truth_parser_class=GroundTruthParser,
    video_dir='sample_video/videos',
    annotations_file='ground_truth.xlsx',
    iou_threshold=0.5,
    confidence_threshold=0.5
)

# Process all videos
results = evaluator.evaluate_all_videos(max_frames_per_video=None)

# Get summary metrics
summary = evaluator.get_summary_metrics()
print(f"F1 Score: {summary['overall_f1_score']:.4f}")
print(f"Precision: {summary['overall_precision']:.4f}")
print(f"Recall: {summary['overall_recall']:.4f}")

# Get detailed results as DataFrame
df_results = evaluator.get_results_dataframe()
```

### 3. Generate Reports

```python
from export_results import EvaluationReporter

reporter = EvaluationReporter(output_dir='evaluation_results')

# Generate all output files (Excel, PDF, JSON)
reporter.generate_complete_report(summary, results, df_results)

# Or individual exports:
reporter.export_summary_excel(summary)
reporter.export_detailed_results_excel(df_results, results)
reporter.generate_plots(summary, results, df_results)
reporter.generate_json_report(summary, results)
```

## Output Files

After running evaluation:

```
evaluation_results/
├── evaluation_summary.xlsx      # Main metrics (formatted, color-coded)
├── evaluation_detailed.xlsx     # Frame-by-frame + per-video results
├── evaluation_plots.pdf         # 9-panel dashboard visualization
└── evaluation_report.json       # Machine-readable results
```

## Key Metrics

| Metric | Formula | Interpretation |
|--------|---------|-----------------|
| **Precision** | TP / (TP + FP) | Of detections, how many correct? |
| **Recall** | TP / (TP + FN) | Of objects, how many detected? |
| **F1 Score** | 2 × P × R / (P + R) | Balanced harmonic mean |
| **IoU** | Intersection / Union | Bounding box overlap |

## Threshold Tuning

### Increase Recall (find more people)
```bash
python evaluate_pipeline.py \
  --annotations ground_truth.xlsx \
  --videos videos/ \
  --confidence 0.3 \
  --iou-threshold 0.3
```

### Increase Precision (fewer false positives)
```bash
python evaluate_pipeline.py \
  --annotations ground_truth.xlsx \
  --videos videos/ \
  --confidence 0.7 \
  --iou-threshold 0.7
```

## Excel Input Format

### Example Annotation File

| video_name | timestamp | event_type | person_id | bbox |
|-----------|-----------|-----------|-----------|------|
| store1_morning.mp4 | 00:05:30 | ENTRY | person_101 | [250,100,350,450] |
| store1_morning.mp4 | 00:05:35 | ENTRY | person_102 | [150,80,220,480] |
| store1_morning.mp4 | 00:07:00 | EXIT | person_101 | [260,110,360,460] |

**Rules:**
- `timestamp`: Format must be HH:MM:SS (max 23:59:59)
- `bbox`: Format [x1,y1,x2,y2] where (x1,y1)=top-left, (x2,y2)=bottom-right
- All fields required, no blank cells
- Video files must exist in videos directory

## Performance Tips

- **GPU acceleration**: Automatically enabled if CUDA available
- **Process subset**: Use `--max-frames 100` for quick testing
- **Memory**: One video processed at a time
- **Speed**: YOLOv8n (~60-100 fps) vs YOLOv8m (~30-50 fps)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Video not found | Check filename matches Excel exactly |
| Timestamp error | Use HH:MM:SS format, no extra spaces |
| Invalid bbox | Format [x1,y1,x2,y2] with 4 numbers |
| CUDA error | Falls back to CPU automatically |
| High memory usage | Reduce `max_frames` or process fewer videos |
| No detections | Lower `confidence` threshold or check video quality |
| All FP (false positives) | Increase confidence or lower IoU threshold |

## Integration Examples

### Save to Database
```python
import requests
import json

# Load results
with open('evaluation_results/evaluation_report.json') as f:
    report = json.load(f)

# Post to API
response = requests.post(
    'http://localhost:8080/api/evaluations',
    json=report
)
```

### Compare Two Runs
```python
from evaluation_utils import ResultsUtilities

results1 = ResultsUtilities.load_evaluation_results('run1')
results2 = ResultsUtilities.load_evaluation_results('run2')

comparison = ResultsUtilities.compare_evaluations(
    results1['summary'],
    results2['summary']
)
print(comparison)
```

### Create Submission File
```python
from evaluation_utils import ResultsUtilities

ResultsUtilities.export_for_submission(
    'evaluation_results',
    'SUBMISSION_Evaluation_Results.xlsx'
)
```

## Batch Processing

```python
from evaluation_utils import batch_validate_videos, batch_validate_annotations

# Validate all videos
video_validation = batch_validate_videos('sample_video/videos')
for video_name, status in video_validation.items():
    print(f"{video_name}: {status['status']}")

# Validate annotations
annotation_validation = batch_validate_annotations(
    'ground_truth.xlsx',
    'sample_video/videos'
)
print(f"Valid: {annotation_validation['valid']}")
print(f"Total annotations: {annotation_validation['total_annotations']}")
```

## Visualization Dashboard

The generated PDF includes 9 charts:

1. **Overall Performance Metrics** - Bar chart (Precision, Recall, F1)
2. **Detection Distribution** - Pie chart (TP, FP, FN)
3. **Per-Video F1** - Horizontal bar chart
4. **Per-Video Precision** - Bar chart
5. **Per-Video Recall** - Bar chart
6. **Cumulative Outcomes** - Line chart over frames
7. **Mean IoU** - Bar chart by video
8. **Detections vs Ground Truth** - Grouped bar chart
9. **Summary Statistics** - Text table

## Data Export Formats

### Excel
- Color-coded metrics (green ≥0.7, yellow ≥0.5, red <0.5)
- Separate sheets for different result types
- Formatted headers and borders

### PDF
- Publication-ready charts and tables
- 300 DPI for printing
- Full-page visualizations

### JSON
- Machine-readable format
- Complete metric preservation
- Easy API integration

---

**For complete documentation, see EVALUATION_README.md**
