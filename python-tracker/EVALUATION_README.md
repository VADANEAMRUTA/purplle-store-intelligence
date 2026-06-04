# Person Detection Evaluation Pipeline

Complete evaluation suite for person detection system against ground truth annotations.

## Overview

This pipeline provides a comprehensive solution for:
- ✅ Parsing ground truth annotations from Excel files
- ✅ Processing videos with your person detector
- ✅ Comparing detections with ground truth using IoU
- ✅ Calculating Precision, Recall, and F1 Score
- ✅ Generating detailed evaluation reports with visualizations
- ✅ Exporting results to Excel for submission

## Scripts

### 1. `parse_ground_truth.py`
**Parse and structure ground truth annotations**

Handles:
- Loading Excel files with annotation data
- Converting timestamps (HH:MM:SS) to milliseconds
- Parsing bounding boxes from multiple formats
- Organizing annotations by video and frame
- Exporting structured data to CSV

**Key Class:** `GroundTruthParser`
- `load_annotations()` - Load from Excel
- `parse_ground_truth()` - Structure annotations
- `get_frame_annotations()` - Query by video/timestamp
- `export_to_csv()` - Export for inspection

### 2. `evaluate_with_ground_truth.py`
**Run detection and compare with ground truth**

Handles:
- Loading your person detector
- Processing videos frame-by-frame
- Running detection on each frame
- Matching detections with ground truth using IoU
- Calculating TP, FP, FN, Precision, Recall, F1

**Key Classes:**
- `BBoxMetrics` - Bounding box calculations
  - `calculate_iou()` - Intersection over Union
  - `match_detections()` - Match by IoU threshold
  
- `PersonDetectionEvaluator` - Main evaluator
  - `process_video()` - Evaluate single video
  - `evaluate_all_videos()` - Batch evaluation
  - `get_summary_metrics()` - Aggregate metrics
  - `get_results_dataframe()` - Results as DataFrame

### 3. `export_results.py`
**Generate reports and visualizations**

Generates:
- Excel files with summary and detailed results
- PDF with 9-panel visualization dashboard
- JSON report for machine-readable format
- Formatted tables with color-coded metrics

**Key Class:** `EvaluationReporter`
- `export_summary_excel()` - Summary metrics
- `export_detailed_results_excel()` - Frame-by-frame results
- `generate_plots()` - Visualization dashboard
- `generate_json_report()` - JSON export
- `generate_complete_report()` - All formats

### 4. `evaluate_pipeline.py`
**Orchestration script combining all steps**

Complete workflow in single command with progress logging.

## Excel Input Format

### Ground Truth Annotations File
Required columns:

| video_name | timestamp | event_type | person_id | bbox |
|-----------|-----------|-----------|-----------|------|
| video1.mp4 | 00:00:05 | ENTRY | person_1 | [100,50,200,300] |
| video1.mp4 | 00:00:07 | ENTRY | person_2 | [150,60,220,310] |
| video1.mp4 | 00:00:10 | EXIT | person_1 | [105,55,205,305] |

**Field Descriptions:**
- `video_name`: MP4 filename
- `timestamp`: HH:MM:SS or HH:MM:SS.sss format
- `event_type`: ENTRY, EXIT, LOITER, etc. (uppercase)
- `person_id`: Unique identifier (person_1, person_2, etc.)
- `bbox`: Bounding box [x1,y1,x2,y2] (top-left and bottom-right corners)

## Output Files

### Generated Reports

```
evaluation_results/
├── evaluation_summary.xlsx          # Summary metrics (formatted)
├── evaluation_detailed.xlsx         # Frame-by-frame and per-video results
├── evaluation_plots.pdf             # 9-panel visualization dashboard
└── evaluation_report.json           # Machine-readable report
```

### Visualizations (evaluation_plots.pdf)

1. **Overall Performance Metrics** - Precision, Recall, F1 Score
2. **Detection Outcomes** - TP/FP/FN distribution pie chart
3. **F1 Score by Video** - Per-video performance
4. **Precision by Video** - Per-video precision values
5. **Recall by Video** - Per-video recall values
6. **Cumulative Outcomes** - TP/FP/FN trends over frames
7. **Mean IoU by Video** - Average bounding box overlap
8. **Detections vs Ground Truth** - Count comparison
9. **Summary Statistics** - Key metrics table

## Metrics Explained

### Precision
- **Formula:** TP / (TP + FP)
- **Meaning:** Of all detected people, how many were correct?
- **Range:** 0-1 (1.0 = perfect)

### Recall
- **Formula:** TP / (TP + FN)
- **Meaning:** Of all ground truth people, how many were detected?
- **Range:** 0-1 (1.0 = perfect)

### F1 Score
- **Formula:** 2 × (Precision × Recall) / (Precision + Recall)
- **Meaning:** Harmonic mean of Precision and Recall
- **Range:** 0-1 (1.0 = perfect)

### IoU (Intersection over Union)
- **Formula:** Intersection Area / Union Area
- **Meaning:** Overlap between predicted and ground truth boxes
- **Range:** 0-1 (1.0 = perfect overlap)
- **Threshold:** Default 0.5 (50% overlap = match)

### Outcomes
- **TP (True Positive):** Correct detection (IoU ≥ threshold)
- **FP (False Positive):** Incorrect detection (IoU < threshold)
- **FN (False Negative):** Missed detection (no match found)

## Usage

### Quick Start

```bash
# Generate sample annotation file
python evaluate_pipeline.py --generate-sample

# Run complete evaluation
python evaluate_pipeline.py \
  --annotations ground_truth.xlsx \
  --videos sample_video/videos \
  --output evaluation_results
```

### Using Individual Scripts

```python
from parse_ground_truth import GroundTruthParser
from evaluate_with_ground_truth import PersonDetectionEvaluator
from export_results import EvaluationReporter
from detector import PersonDetector

# Step 1: Parse ground truth
parser = GroundTruthParser('ground_truth.xlsx')
parser.load_annotations()
ground_truth = parser.parse_ground_truth()

# Step 2: Run evaluation
evaluator = PersonDetectionEvaluator(
    detector_class=PersonDetector,
    ground_truth_parser_class=GroundTruthParser,
    video_dir='videos/',
    annotations_file='ground_truth.xlsx',
    iou_threshold=0.5,
    confidence_threshold=0.5
)

results = evaluator.evaluate_all_videos()
summary = evaluator.get_summary_metrics()
frame_results_df = evaluator.get_results_dataframe()

# Step 3: Generate reports
reporter = EvaluationReporter('evaluation_results')
reporter.generate_complete_report(summary, results, frame_results_df)
```

### Command Line Options

```
--annotations FILE              Path to ground truth Excel file
--videos DIR                   Directory with video files
--output DIR                   Output directory for results
--iou-threshold FLOAT          IoU threshold for matching (0-1, default: 0.5)
--confidence FLOAT             Detection confidence threshold (0-1, default: 0.5)
--max-frames INT               Max frames per video (default: all)
--generate-sample              Generate sample annotation file
```

## Configuration

### Adjusting Sensitivity

**Lower confidence threshold** = More detections, higher recall but lower precision
```bash
python evaluate_pipeline.py \
  --annotations ground_truth.xlsx \
  --videos videos/ \
  --confidence 0.3  # More sensitive (default: 0.5)
```

**Higher IoU threshold** = Stricter bounding box matching
```bash
python evaluate_pipeline.py \
  --annotations ground_truth.xlsx \
  --videos videos/ \
  --iou-threshold 0.7  # Stricter (default: 0.5)
```

## Integration with Spring Boot API

Export evaluation results for storage:

```python
import requests
import pandas as pd

# Load results
df_results = pd.read_excel('evaluation_results/evaluation_detailed.xlsx', 
                           sheet_name='Video Summary')

# Post to your API
for idx, row in df_results.iterrows():
    payload = {
        'video_name': row['Video Name'],
        'precision': float(row['Precision']),
        'recall': float(row['Recall']),
        'f1_score': float(row['F1 Score']),
        'tp': int(row['TP']),
        'fp': int(row['FP']),
        'fn': int(row['FN'])
    }
    response = requests.post('http://localhost:8080/api/evaluations', json=payload)
```

## Troubleshooting

### Common Issues

**"Video not found"**
- Verify video filename matches exactly in Excel
- Check video files are in the correct directory

**"Could not parse timestamp"**
- Ensure timestamp format is HH:MM:SS or HH:MM:SS.sss
- No extra spaces around timestamp

**"Invalid bbox format"**
- Format must be [x1,y1,x2,y2] or x1,y1,x2,y2
- Coordinates must be valid numbers

**"No detections in video"**
- Check detector confidence threshold (too high?)
- Verify detector is working correctly
- Check video quality/resolution

### Enabling Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Notes

- **Processing speed depends on:** Video resolution, frame count, detector model
- **GPU acceleration:** Automatically enabled if CUDA available
- **Memory:** Load one video at a time to minimize memory usage
- **Max frames option:** Use for quick testing on subset of video

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python evaluate_pipeline.py --generate-sample
```

## Dependencies

- `opencv-python` - Video processing
- `numpy` - Numerical operations
- `pandas` - Data handling
- `openpyxl` - Excel export
- `matplotlib` - Visualizations
- `scikit-learn` - Metrics calculation
- `ultralytics` - YOLOv8 detector
- `Pillow` - Image processing

## Example Workflow

```bash
# 1. Create sample annotation file
python evaluate_pipeline.py --generate-sample

# 2. Edit sample_annotations.xlsx with your actual data

# 3. Run evaluation pipeline
python evaluate_pipeline.py \
  --annotations sample_annotations.xlsx \
  --videos sample_video/videos \
  --output my_evaluation_results

# 4. Review results
# - Open my_evaluation_results/evaluation_summary.xlsx
# - View charts in my_evaluation_results/evaluation_plots.pdf
# - Check detailed metrics in my_evaluation_results/evaluation_detailed.xlsx
# - Parse JSON at my_evaluation_results/evaluation_report.json
```

## Next Steps

- Review generated reports and metrics
- Adjust confidence/IoU thresholds based on requirements
- Export final results to Excel for submission
- Integrate with Spring Boot API for persistence

---

**Created for Purplle Store Intelligence System**
Person Detection Evaluation Pipeline
